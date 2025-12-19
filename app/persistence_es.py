from elasticsearch import Elasticsearch
import os

ES_URL = os.environ.get("ES_URL", "http://localhost:9200")
es = Elasticsearch([ES_URL])

INDEX = os.environ.get("ES_INDEX", "email_verifications")

def index_verification(doc: dict):
    resp = es.index(index=INDEX, document=doc)
    return resp
