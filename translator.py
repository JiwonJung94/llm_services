from langchain.prompts import PromptTemplate
from langchain.schema.messages import HumanMessage, SystemMessage, AIMessage
import json
import re
from utils.history_buffer import HistoryBuffer

system_message = SystemMessage(content = """
**Enhanced Translation Task Instructions**

Welcome to your translation task. You are about to embark on a journey of bridging languages by translating text within a specified range. This task emphasizes precision and cultural sensitivity, ensuring the message traverses linguistic boundaries intact.

**Task Overview:**

- **Input Language:** The original language of the text.
- **Output Language:** The language into which you are translating the text.
- **Translation Range:** The exact portion of text assigned for translation.
- **Contextual Framework:** Background information and any translations up to the current segment, vital for seamless continuity and accuracy.

**Core Principles:**

1. **Comprehension Before Translation:** Fully understand the source text's meaning, context, nuances, and intended message. This understanding forms the foundation of a successful translation, ensuring accuracy and avoiding the pitfalls of literal translations.

2. **Fluency and Localization:** Adapt the translation to flow naturally in the target language, respecting its cultural, linguistic norms, and sensitivities. Your translation should read as if originally written in the target language.

3. **Consistency and Accuracy:** Maintain uniformity in terminology, style, tone, and other elements throughout your translation. Ensure the translation is a faithful representation of the original message without distortions, omissions, or unwarranted additions.

4. **Preservation of Original Terms for Specialized Vocabulary:** When it comes to technical terms, professional jargon, or any specialized vocabulary, retain the original terms. This approach ensures that the translation remains accurate and understandable to readers familiar with the subject matter.

5. **Engage with the Content:** Reflect on the cultural implications and potential sensitivities of the translation. Localization involves more than language conversion; it's about making the content resonate with the target audience culturally and emotionally.

**Your Responsibilities:**

1. Translate **only** the designated "translation range."
2. Stay within the bounds of the specified segment, refraining from translating beyond.
3. Deliver a translation that mirrors the original's meaning and tone, without insertions or exclusions.
4. Present your translation in a clean, JSON object format for clarity and consistency.

**Submission Format:**

Please submit your translated text in a JSON format. This format aids in maintaining clarity and ensures a structured presentation of your translation. Here is how you should structure your submission:

```json
{
    "translated_text": "Insert your translation here."
}
```

Adhere strictly to the format above. Your translation should be the sole content within the JSON object, without any supplementary remarks or alterations to the format.
""")

human_message_template = """
<translation range>
{target}
</translation range>

<input language>
{input_language}
</input language>

<output language>
{output_language}
</output language>

<preceding context>
{preceding_context}
</preceding context>

translation output for the specified translation range:
"""

human_message_prompt_template = PromptTemplate(
    input_variables = ["target", "input_language", "output_language", "preceding_context"],
    template = human_message_template
)

class Translator:
    def __init__(self, chat_model, preceding_context_length=10, history_file_path=None):
        #  Initializes the Translator with a chat model, an optional preceding context length, 
        #  and an optional path to a history file for persisting translation history.
        #  
        #  Parameters:
        #      chat_model: The chat model to use for generating translations.
        #      preceding_context_length (int): The number of preceding messages to include for context.
        #      history_file_path (str, optional): The path to a file for saving translation history.
        
        self.chat_model = chat_model
        self.history_buffer = HistoryBuffer(preceding_context_length, history_file_path)

    def translate(self, target, input_language, output_language, include_preceding_context=True):
        #  Translates the given target text from the input language to the output language,
        #  optionally including preceding context for better translation quality.
        #  
        #  Parameters:
        #      target (str): The text to be translated.
        #      input_language (str): The language of the input text.
        #      output_language (str): The language to translate the text into.
        #      include_preceding_context (bool): Whether to include preceding context in the translation request.
        #  
        #  Returns:
        #      dict: A dictionary containing the original text and the translated text.

        preceding_context = ""
        if include_preceding_context:
            preceding_context = self.history_buffer.get()

        # Format the human message using a template
        human_message = HumanMessage(content=human_message_prompt_template.format(
            target=target.strip(), 
            input_language=input_language, 
            output_language=output_language, 
            preceding_context=str(preceding_context)
        ))
        messages = [system_message, human_message]

        # Invoke the chat model to get the translation
        chain = self.chat_model
        ai_message = chain.invoke(messages)

        # Extract translated text from the AI message using a regex pattern
        pattern = re.compile(r'\{.*?\}(?=\s*\{|$)', re.DOTALL)
        matched_jsons = pattern.findall(ai_message.content)

        translated_text = []
        for js in matched_jsons:
            try:
                parsed_json = json.loads(js)
                if "translated_text" in parsed_json and isinstance(parsed_json["translated_text"], str):
                    translated_text.append(parsed_json["translated_text"])
                else:
                    translated_text = None
                    break
            except:
                translated_text = None
                break
        
        if translated_text is None:
            translated_text = target # Fallback to the original text if translation fails
        else:
            translated_text = '\n'.join(translated_text)
        
        # Prepare the result dictionary
        result = {
            "original_text": target,
            "translated_text": translated_text
        }

        # Push the result to the history buffer for future context
        self.history_buffer.push(str(result))

        return result



if __name__ == "__main__":
    from langchain_community.llms import Ollama
    from langchain_community.chat_models import ChatOllama
    from translator import *
    
    chat_model = ChatOllama(base_url="http://localhost:11434", model="neural-chat:7b-v3.3-q6_K", temperature=0)
    history_file_path = "./translate_history.txt"
    
    translator = Translator(chat_model, 10, history_file_path)
    
    sentences = [
        "Lorsque j’avais six ans j’ai vu, une fois, une magnifique image, dans un livre sur la Forêt Vierge qui s’appelait « His- toires Vécues ». Ça représentait un serpent boa qui avalait un fauve. Voilà la copie du dessin.",
        "On disait dans le livre : « Les serpents boas avalent leur proie tout entière, sans la mâcher. Ensuite ils ne peuvent plus bouger et ils dorment pendant les six mois de leur digestion. » J’ai alors beaucoup réfléchi sur les aventures de la jungle et, à mon tour, j’ai réussi, avec un crayon de couleur, à tracer mon premier dessin. Mon dessin numéro 1. Il était comme ça :",
        "J’ai montré mon chef-d’œuvre aux grandes personnes et je leur ai demandé si mon dessin leur faisait peur."
    ]
    
    
    for sentence in sentences:
        result = translator.translate(target=sentence, input_language="Auto Detect", output_language="Korean", include_preceding_context=False)
        print("Original Text:", result["original_text"])
        print("Translated Text:", result["translated_text"])
        print("---")