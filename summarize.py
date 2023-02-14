from bson import ObjectId
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain import OpenAI, PromptTemplate, LLMChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.mapreduce import MapReduceChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import pymongo
load_dotenv()

conn_str = os.getenv("MONGO_URL")
# set a 5-second connection timeout
client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=5000)

try:
    print(client.server_info())
    print("Connected to the server.")
except Exception:
    print("Unable to connect to the server.")

mongo = client.get_database('eventbot')


llm = OpenAI(temperature=0)

text_splitter = CharacterTextSplitter()

# with open('state_of_the_union.txt') as f:
#     state_of_the_union = f.read()
# texts = text_splitter.split_text(state_of_the_union)


page_data = mongo.db.page_data.find_one(
    {"_id": ObjectId("63e521413474e39cb6ef93a5")})
# convert to txt format

text_page = str(page_data['events'])


split_data = text_splitter.split_text(text_page)
docs = [Document(page_content=t) for t in split_data[:3]]
prompt_template = """Write a concise summary of these events that happened on a web page. They are in chronological order.:


{text}


CONCISE SUMMARY FON NON-TECHINCAL USER:"""
PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
chain = load_summarize_chain(OpenAI(temperature=0), chain_type="map_reduce",
                             return_intermediate_steps=True, map_prompt=PROMPT, combine_prompt=PROMPT)

print(chain({"input_documents": docs}, return_only_outputs=True))
