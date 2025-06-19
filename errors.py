""" This module contains error types used across multiple other modules """

class APIError(Exception):
    """ Custom error made to be displayed to users at API-level"""
    status_code = 400

    def __init__(self, message, status_code=None, **kwargs):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = kwargs

    def to_dict(self):
        dictionary = dict(self.payload or ())
        dictionary['message'] = self.message
        return dictionary
    
    def __str__(self):
        return ", ".join(f"{key}={value}" for key, value in self.to_dict().items())