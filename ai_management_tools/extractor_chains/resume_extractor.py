import time
 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from typing import List, Optional
from langchain.chains.openai_tools import create_extraction_chain_pydantic
from langchain_core.pydantic_v1 import BaseModel
from langchain_openai import ChatOpenAI
from decouple import config
from django.core.files.uploadedfile import InMemoryUploadedFile
import io
from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser
from langchain.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader

import tempfile
import os
from rest_framework.permissions import AllowAny
import uuid
from datetime import datetime, timedelta
import concurrent.futures
 
 
class EmployementDetails(BaseModel):
    company_name:Optional[str]=None
    total_experience:Optional[str]=None
 
class ExtractInfo(BaseModel):
    raw_name:Optional[str]=None
    first_name: Optional[str]=None
    last_name:Optional[str]=None
    age: Optional[int] = None
    phone_no:Optional[int]= None    
    address:Optional[str]= None
    email:Optional[str]= None
    experience_duration_years:Optional[float] =None
    projects:Optional[str]=None
    certifications:Optional[str]=None
    skills:Optional[str]=None
    additional_skills_tools:Optional[str]=None
    universities:Optional[str]=None
    achievements:Optional[str]=None
    extra_activities:Optional[str]=None
    linkedin_url:Optional[str]=None
    employement_details:Optional[List[EmployementDetails]]=[]
    
 
class ResumeInfoAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        print("hitting extractor chain--------------------->")
        try:
            SECRET_KEY = config('OPENAI_SECRET_KEY')
            resume = request.FILES.get('resume')

 
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(resume.read())
                temp_file_path = temp_file.name
 
            extension = resume.name.split('.')[-1]
            loader=self.getDocumentData(temp_file_path,extension)
            docs = loader.load_and_split()
            os.remove(temp_file_path)
 
            llm = ChatOpenAI(openai_api_key=SECRET_KEY, model='gpt-4o',temperature=0)
            chain = create_extraction_chain_pydantic(ExtractInfo, llm)
            startTime=time.time()
            response = chain.invoke(docs)
            endTime=time.time()
            response_time=(float)((endTime-startTime))
 
            combined_info = ExtractInfo()
            
            if isinstance(response, list):
                for item in response:
                    data = item.dict()
                    keys = list(data.keys())
                    for key in keys:
                        value = data[key]
                        if key == "raw_name" and value:
                            raw_name = value.split(" ")
                            data["first_name"] = raw_name[0]
                            data["last_name"] = " ".join(raw_name[1:]) if len(raw_name) > 1 else None
                        if value is not None:
                            setattr(combined_info, key, data[key])
 
            elif isinstance(response, ExtractInfo):
                combined_info = response
            
            host=request.get_host()
            combined_info_dict = combined_info.dict()
  
            return Response({"candidate_info": combined_info_dict}, status=status.HTTP_200_OK)
        
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
    @staticmethod
    def getDocumentData(temp_file_path,extension):
        if extension == 'pdf':
            loader_data = PyPDFLoader(temp_file_path)
        elif extension == 'docx' or extension == 'doc':
            loader_data = Docx2txtLoader(temp_file_path)
        return loader_data
 