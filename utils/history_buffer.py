import os

class HistoryBuffer:
    """
    A class to manage a history buffer, which stores a limited number of recent entries.
    Entries can be stored in memory and optionally in a file for persistence.

    Attributes:
        buffer_size (int): The maximum number of entries to store in the buffer.
        file_path (str, optional): Path to the file where entries are persisted. If None, persistence is disabled.
        delimiter (str): The delimiter used to separate entries in the file.

    Methods:
        push(content): Adds an entry to the buffer and file (if file_path is provided).
        get(max_length=None): Retrieves the last 'max_length' entries from the buffer.
    """
    def __init__(self, buffer_size=10, file_path=None, delimiter="\n____I_LOVE_YOU_HUYEN____"):
        if not isinstance(buffer_size, int) or buffer_size < 0:
            raise TypeError("buffer_size must be a non-negative integer")

        if file_path is not None:
            if not isinstance(file_path, str):
                raise ValueError("file_path must be a string")
        
        if not isinstance(delimiter, str) or len(delimiter) < 1:
                raise ValueError("delimiter must be a string with a length of at least 1")

        self._file_path = file_path
        self._delimiter = delimiter
        self._buffer_size = buffer_size

        # Initialize the buffer by reading from the file, if available and buffer_size is positive
        if file_path and buffer_size > 0:
            self._buffer = self.__read_file()[-self._buffer_size:]
        else:
            self._buffer = []
    
    def __flush_to_file(self, content):
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
        with open(self._file_path, 'a', encoding='utf-8') as file:
            file.write(self._delimiter)
            file.write(content)

    def __read_file(self):
        # Attempt to read the file and split entries by the delimiter
        try:
            with open(self._file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                entries = content.split(self._delimiter)
                return entries[1:] # Ignore anything before the first delimiter
        except:
            return [] # Return an empty list if reading fails
    
    def push(self, content):
        if not isinstance(content, str):
            raise TypeError("content must be a string")

        # Append content to buffer, maintaining the buffer_size limit
        if self._buffer_size > 0:
            self._buffer.append(content)
            self._buffer = self._buffer[-self._buffer_size:]
 
        # Flush content to file, if file_path is set and content does not contain the delimiter
        if self._file_path is not None:
            if self._delimiter in content:
                raise ValueError(f"content must not contain the delimiter: {self._delimiter}")
            self.__flush_to_file(content=content)
    
    def get(self, max_length=None):
        if max_length is not None:
            if not isinstance(max_length, int) or max_length < 0:
                raise ValueError("max_length must be a non-negative integer or None")
        else:
            max_length = self._buffer_size
        
        if max_length == 0:
            return []

        # Retrieve the last 'max_length' entries from the buffer or file
        if max_length <= len(self._buffer) or self._file_path is None:
            return self._buffer[-max_length:]

        # Read from the file if needed
        return self.__read_file()[-max_length:]



if __name__ == "__main__":
    # Test cases for HistoryBuffer

    # Create a buffer with default settings
    buffer = HistoryBuffer()

    # Push some entries into the buffer
    print("Pushing entries...")
    for i in range(15):
        buffer.push(f"Entry {i}")

    # Retrieve buffered items
    print("\nRetrieving buffered entries:")
    entries = buffer.get()
    for entry in entries:
        print(entry)

    # Retrieve and print the last 5 entries
    print("\nRetrieving the last 5 entries:")
    entries = buffer.get(5)
    for entry in entries:
        print(entry)

    # Test with file persistence (if desired, replace 'test_history.txt' with a preferred file path)
    file_path = "./test_history.txt"
    buffer_with_file = HistoryBuffer(buffer_size=5, file_path=file_path)

    # Push entries to the buffer with file persistence
    print("\nPushing entries with file persistence...")
    for i in range(10):
        buffer_with_file.push(f"File Entry {i}")

    # Simulate a restart by creating a new buffer instance with the same file
    print("\nSimulating a restart (reloading from file)...")
    buffer_reloaded = HistoryBuffer(buffer_size=5, file_path=file_path)

    # Retrieve and print entries from the reloaded buffer
    print("Entries from reloaded buffer:")
    reloaded_entries = buffer_reloaded.get(7)
    for entry in reloaded_entries:
        print(entry)

    # Cleanup test file (uncomment if you want to remove the file after tests)
    # os.remove(file_path)
