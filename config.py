from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConflictError

ES = 'localhost:9200'
es = Elasticsearch(ES)
