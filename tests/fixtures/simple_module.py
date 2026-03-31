import os
from pathlib import Path

GLOBAL_VAR = 42

def helper(x):
    return x * 2

def process(data):
    result = helper(data)
    cleaned = clean(result)
    return cleaned

def clean(value):
    return str(value).strip()

class Processor:
    def __init__(self, config):
        self.config = config

    def run(self, data):
        intermediate = self.preprocess(data)
        return process(intermediate)

    def preprocess(self, data):
        return helper(data)
