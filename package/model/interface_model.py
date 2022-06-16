class InterfaceModel:
    def __init__(self) -> None:
        pass

    def get_list_of_paths(self, directory: str) -> list:
        '''
        override to provide respective functionality
        '''

    def delete(self, path: str) -> None:
        '''
        override to provide respective functionality
        '''

    def move(self, path: str, new_path: str) -> None:
        '''
        override to provide respective functionality
        '''

    def open_path(self, path: str) -> None:
        '''
        override to provide respective functionality
        '''