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


    def __init__(
                    self,
                    xml_describtion_path, 
                    xml_file_path, 
                    openai_api_key_azure= OPENAI_API_KEY_AZURE,
                    openai_api_version= OPENAI_API_VERSION,
                    openai_api_base= OPENAI_API_BASE) -> None:
        
        self.xml_describtion_path = xml_describtion_path
        self.xml_file_path = xml_file_path
        self.openai_api_key_azure = openai_api_key_azure
        self.openai_api_version = openai_api_version
        self.openai_api_base = openai_api_base

        with open(self.xml_file_path, 'rb') as f:
            self.xml_file = lxml.etree.fromstring(f.read())
        

    def parsing_promt(self) -> str:
        with open(self.xml_describtion_path, 'r', encoding='utf-8') as f:
            promt = f.read()
        return promt

    def query(self, user_promt: str) -> str:
        
        promt = self.parsing_promt()

        client = AzureOpenAI(
                api_key=self.openai_api_key_azure,
                api_version=self.openai_api_version,
                azure_endpoint=self.openai_api_base
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
                'content': user_promt, # 'Какие есть авто, у которых меньше 4 дверей?'
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
    
    def parsing_xpath(self, user_promt: str):
        answer = self.query(user_promt) # возможно надо перенести этот метод в query
        m = re.search('```xpath\n(//offer\[.+\]).*?```', answer, flags=re.DOTALL)
        if m is None:
            return answer, False
        else:
            xpath = m.group(1)
            return xpath, True

    def recursive_dict(self, element):
            if element.text == None and len(element.attrib):
                return element.tag, element.attrib
            return element.tag, \
                            dict(map(self.recursive_dict, element)) or element.text  

    def __call__(self, user_promt: str) -> list :
        xml_file = self.xml_file
        xpath, flag = self.parsing_xpath(user_promt)
        if flag:
            offers_res = xml_file.xpath(xpath)
            offers_list = [self.recursive_dict(offer)[1] for offer in offers_res]
            return offers_list
        elif not flag:
            return xpath

    def xml_to_json(self, xml_list):
        return json.dumps(xml_list, indent=4, ensure_ascii=False)