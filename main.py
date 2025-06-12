from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from sqlalchemy import Column, Integer, create_engine, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()


app=FastAPI()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
Base = declarative_base()


class PDFFile(Base):
    __tablename__ = "pdf_files"
    id= Column(Integer,primary_key= True, index=True)
    filename = Column(String)
    data = Column(LargeBinary)

Base.metadata.create_all(bind=engine)


def get_db():
    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield db
    finally:
        db.close()


@app.post("/")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        pdf_file = PDFFile(filename=file.filename, data=contents)
        db.add(pdf_file)
        db.commit()
        db.refresh(pdf_file)
        print("Susess")
        return {"message": "PDF uploaded successfully", "file_id": pdf_file.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
