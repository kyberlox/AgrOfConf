from elasticsearch import Elasticsearch

import os
from dotenv import load_dotenv
import time

load_dotenv()

pswd = os.getenv('pswd')

def create_elastic_client():
    max_retries = 5
    retry_delay = 15
    
    for i in range(max_retries):
        try:
            elastic_client = Elasticsearch(hosts=["http://elasticsearch:9200"], basic_auth=('elastic', pswd), verify_certs=False, request_timeout=100)


            if elastic_client.ping():
                print("✅ Успешное подключение Elasticsearch!")
                return elastic_client
        except Exception as e:
            print(f"❌ Connection attempt {i+1}/{max_retries} failed: {e}")
            if i < max_retries - 1:
                time.sleep(retry_delay)
    

elastic_client = create_elastic_client()