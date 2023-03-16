from textwrap3 import wrap
from flask import session

# def mcq():
text=session['t_data']
print(text)
# text= """ can get more time for core business tasks due to the instant availability of new features and services in AWS.
# It provides effortless hosting of legacy applications. AWS does not require learning new technologies and migration of applications to the AWS provides the advanced computing and efficient storage.
# AWS also offers a choice that whether we want to run the applications and services together or not. We can also choose to run a part of the IT infrastructure in AWS and the remaining part in data centres."""
for wrp in wrap(text,150):
  print(wrp)
print("\n")

import torch
from transformers import T5ForConditionalGeneration,T5Tokenizer
summary_model=T5ForConditionalGeneration.from_pretrained('t5-base')
summary_tokenizer=T5Tokenizer.from_pretrained('t5-base')

device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
summary_model=summary_model.to(device)

import random 
import numpy as np

def set_seed(seed: int):
  random.seed(seed)
  np.random.seed(seed)
  torch.manual_seed(seed)
  torch.cuda.manual_seed_all(seed)

set_seed(42)




import nltk
#nltk.download('punkt')
#nltk.download('brown')
#nltk.download('wordnet')
from nltk.corpus import wordnet as wn
from nltk.tokenize import sent_tokenize

def postprocesstext(content):
  final=""
  for sent in sent_tokenize(content):
    sent=sent.capitalize()
    final=final+" "+sent
  return final

def summarizer(text,model,tokenizer):
  text=text.strip().replace("\n"," ")
  text="summarize: "+text
  max_len=512
  encoding = tokenizer.encode_plus(text,max_length=max_len,pad_to_max_length=False,truncation=True,return_tensors="pt").to(device)
  input_ids,attention_mask=encoding["input_ids"],encoding["attention_mask"]

  outs=model.generate(input_ids=input_ids,
                      attention_mask=attention_mask,
                      early_stopping=True,
                      num_beams=3,
                      num_return_sequences=1,
                      no_repeat_ngram_size=2,
                      min_length=75,
                      max_length=300)
  dec=[tokenizer.decode(ids,skip_special_tokens=True) for ids in outs]
  summary=dec[0]
  summary=postprocesstext(summary)
  summary=summary.strip()

  return summary


summarized_text=summarizer(text,summary_model,summary_tokenizer)

print("\noriginal Text >>")
for wrp in wrap(text,150):
  print(wrp)
print("\n")
print("Summarized Text >>")
for wrp in wrap(summarized_text,200):
  print(wrp)
print("\n")



import nltk
#nltk.download('stopwords')
from nltk.corpus import stopwords
import string
import pke
import traceback

def get_nouns_multipartite(content):
  out=[]
  try:
    extractor=pke.unsupervised.MultipartiteRank()
    stoplist=list(string.punctuation)
    stoplist+=['-lrb-','-rrb-','-lcb-','-rcb-','-lsb-','-rsb-']
    stoplist+=stopwords.words('english')
    extractor.load_document(input=content,stoplist=stoplist)
    pos={'PROPN','NOUN','ADJ'}
    extractor.candidate_selection(pos=pos)

    extractor.candidate_weighting(alpha=1.1,
                                  threshold=0.74,
                                  method='average')
    
    keyphrases=extractor.get_n_best(n=12)

    for val in keyphrases:
      out.append(val[0])
  except:
    out=[]
    traceback.print_exc()
  return out


from flashtext import KeywordProcessor

def get_keywords(originaltext,summarytext):
  keywords=get_nouns_multipartite(originaltext)
  print("keywords unsummarized: ",keywords)
  keyword_processor=KeywordProcessor()
  for keyword in keywords:
    keyword_processor.add_keyword(keyword)
  
  keywords_found=keyword_processor.extract_keywords(summarytext)
  keywords_found=list(set(keywords_found))
  print("keywords_ found in summarized: ",keywords_found)

  important_keywords=[]
  for keyword in keywords:
    if keyword in keywords_found:
      important_keywords.append(keyword)
  return important_keywords
imp_keywords=get_keywords(text,summarized_text)
print(imp_keywords)


question_model=T5ForConditionalGeneration.from_pretrained('ramsrigouthamg/t5_squad_v1')
question_tokenizer=T5Tokenizer.from_pretrained('ramsrigouthamg/t5_squad_v1')
question_model=question_model.to(device)

def get_question(context,answer,model,tokenizer):
  text="context: {} answer: {}".format(context,answer)
  encoding = tokenizer.encode_plus(text,max_length=384,pad_to_max_length=False,truncation=True,return_tensors="pt").to(device)
  input_ids,attention_mask=encoding["input_ids"],encoding["attention_mask"]

  outs=model.generate(input_ids=input_ids,
                      attention_mask=attention_mask,
                      early_stopping=True,
                      num_beams=5,
                      num_return_sequences=1,
                      no_repeat_ngram_size=2,
                      max_length=72)
  dec=[tokenizer.decode(ids,skip_special_tokens=True) for ids in outs]
  Question=dec[0].replace("question:","")
  Question=Question.strip()
  return Question

for wrp in wrap(summarized_text,150):
  print(wrp)
print("\n")
ques_list=[]
answer_list=[]
for answer in imp_keywords:
  ques=get_question(summarized_text,answer,question_model,question_tokenizer)
  ques_list.append(ques)
  print(ques)
  answer_list.append(answer)
  print(answer.capitalize())
  print("\n")