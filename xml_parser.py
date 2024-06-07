from openai import AzureOpenAI
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
import re
import lxml.etree
import json

class GPT4XmlParser:

    OPENAI_API_KEY_AZURE = '3983fb5f29ba4c39b74c2beb404e1ca4'
    OPENAI_API_VERSION = '2023-07-01-preview'
    OPENAI_API_BASE = 'https://gradient.openai.azure.com/'


    def __init__(self, system_prompt_path, xml_file_path) -> None:
        self.system_prompt_path = system_prompt_path
        self.xml_file_path = xml_file_path

    def __call__(self, user_promt: str) :
        self.user_promt = user_promt
        return self.search_candidates()

    def parsing_promt(self) -> str:
        with open(self.system_prompt_path, 'r', encoding='utf-8') as f:
            promt = f.read()
        return promt

    def query(self) -> str:
        
        promt = self.parsing_promt()

        client = AzureOpenAI(
                api_key=self.OPENAI_API_KEY_AZURE,
                api_version=self.OPENAI_API_VERSION,
                azure_endpoint=self.OPENAI_API_BASE
            )
        
        kwargs = {
                'ai_model': 'gradient-gpt-4-8',
                '_prompt': '',
                'temperature': 0.2,
                'max_tokens': 200,
                'top_p': 0.0,
                'frequency_penalty': 0.0,
                'presence_penalty': -0.5
            }
        user = {
                'role': 'user',
                'content': self.user_promt, # 'Какие есть авто, у которых меньше 4 дверей?'
            }
        kwargs['_prompt'] = [
                {'role': 'system',
                'content': [
                    'Напиши xpath-запрос к xml, который вернет элементы offer, подходящие пользователю.\n'
                    'Описание XML:\n'
                    f'{promt}'
                    'Конец XML'
                ][0]
                },
                user
            ]

        response = client.chat.completions.create(
                model=kwargs['ai_model'],
                messages=kwargs['_prompt'],
                temperature=float(kwargs['temperature']),
                max_tokens=2000,
                top_p=kwargs['top_p'],
                frequency_penalty=kwargs['frequency_penalty'],
                presence_penalty=kwargs['presence_penalty'],
                timeout=40
            )
        answer = response.choices[0].message.content

        return answer 
    
    def read_xml(self):
        with open(self.xml_file_path, 'rb') as f:
            root = lxml.etree.fromstring(f.read())
        return root
    
    def parsing_xpath(self) -> str:
        answer = self.query() # возможно надо перенести этот метод в query
        m = re.search('```xpath\n(//offer\[.+\]).*?```', answer, flags=re.DOTALL)
        xpath = m.group(1)
        return xpath

    def recursive_dict(self, element):
            if element.text == None and len(element.attrib):
                return element.tag, element.attrib
            return element.tag, \
                            dict(map(self.recursive_dict, element)) or element.text  

    def search_candidates(self) -> list:
        root = self.read_xml()
        xpath = self.parsing_xpath()
        offers_res = root.xpath(xpath)
        offers_list = [self.recursive_dict(offer)[1] for offer in offers_res]
        return offers_list

    def xml_to_json(self, xml_list):
        return json.dumps(xml_list, indent = 4) 