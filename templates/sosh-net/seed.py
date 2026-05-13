#! /usr/bin/env python3
from mapp.types import *
from mapp.context import get_context_from_env, spec_from_env

from dotenv import load_dotenv



def main():
	load_dotenv()
	context = get_context_from_env()
	spec = spec_from_env()
	print('Context:')
	print(context)
	print('Spec:')
	print(spec)

if __name__ == '__main__':
	main()
