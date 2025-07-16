import os
import logging
from pathlib import Path
from typing import Dict, Optional
from PyPDF2 import PdfReader

class FileCacheManager:
    """
    Manages in-memory caching of job descriptions and resumes from folders.
    """
    
    def __init__(self, jd_folder: str, resume_folder: str):
        """
        Initialize the FileCacheManager.
        
        Args:
            jd_folder: Path to the job descriptions folder
            resume_folder: Path to the resumes folder
        """
        self.jd_folder = Path(jd_folder)
        self.resume_folder = Path(resume_folder)
        
        # In-memory caches
        self.jd_cache: Dict[str, str] = {}
        self.resume_cache: Dict[str, str] = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load files into cache
        self._load_jd_files()
        self._load_resume_files()
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text content
        """
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    def _load_text_file(self, file_path: Path) -> str:
        """
        Load text content from a text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            str: File content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            self.logger.error(f"Error reading text file {file_path}: {e}")
            return ""
    
    def _load_jd_files(self):
        """Load all job description files into cache."""
        if not self.jd_folder.exists():
            self.logger.warning(f"JD folder does not exist: {self.jd_folder}")
            return
        
        self.logger.info(f"Loading job descriptions from: {self.jd_folder}")
        
        # Load PDF files
        for pdf_file in self.jd_folder.glob("*.pdf"):
            file_name = pdf_file.stem  # filename without extension
            content = self._extract_text_from_pdf(pdf_file)
            if content:
                self.jd_cache[file_name] = content
                self.logger.debug(f"Loaded JD: {file_name}")
        
        # Load text files
        for txt_file in self.jd_folder.glob("*.txt"):
            file_name = txt_file.stem  # filename without extension
            content = self._load_text_file(txt_file)
            if content:
                self.jd_cache[file_name] = content
                self.logger.debug(f"Loaded JD: {file_name}")
        
        self.logger.info(f"Loaded {len(self.jd_cache)} job descriptions into cache")
    
    def _load_resume_files(self):
        """Load all resume files into cache."""
        if not self.resume_folder.exists():
            self.logger.warning(f"Resume folder does not exist: {self.resume_folder}")
            return
        
        self.logger.info(f"Loading resumes from: {self.resume_folder}")
        
        # Load PDF files
        for pdf_file in self.resume_folder.glob("*.pdf"):
            file_name = pdf_file.stem  # filename without extension
            content = self._extract_text_from_pdf(pdf_file)
            if content:
                self.resume_cache[file_name] = content
                self.logger.debug(f"Loaded resume: {file_name}")
        
        # Load text files
        for txt_file in self.resume_folder.glob("*.txt"):
            file_name = txt_file.stem  # filename without extension
            content = self._load_text_file(txt_file)
            if content:
                self.resume_cache[file_name] = content
                self.logger.debug(f"Loaded resume: {file_name}")
        
        self.logger.info(f"Loaded {len(self.resume_cache)} resumes into cache")
    
    def get_jd_content(self, jd_name: str) -> Optional[str]:
        """
        Get job description content by name.
        
        Args:
            jd_name: Name of the job description file (without extension)
            
        Returns:
            str: Job description content or None if not found
        """
        return self.jd_cache.get(jd_name)
    
    def get_resume_content(self, resume_name: str) -> Optional[str]:
        """
        Get resume content by name.
        
        Args:
            resume_name: Name of the resume file (without extension)
            
        Returns:
            str: Resume content or None if not found
        """
        return self.resume_cache.get(resume_name)
    
    def get_all_jd_names(self) -> list[str]:
        """
        Get all available job description names.
        
        Returns:
            list[str]: List of job description names
        """
        return list(self.jd_cache.keys())
    
    def get_all_resume_names(self) -> list[str]:
        """
        Get all available resume names.
        
        Returns:
            list[str]: List of resume names
        """
        return list(self.resume_cache.keys())
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, int]: Cache statistics
        """
        return {
            "jd_count": len(self.jd_cache),
            "resume_count": len(self.resume_cache),
            "total_files": len(self.jd_cache) + len(self.resume_cache)
        }
    
    def refresh_cache(self):
        """Refresh the cache by reloading all files."""
        self.logger.info("Refreshing file cache")
        self.jd_cache.clear()
        self.resume_cache.clear()
        self._load_jd_files()
        self._load_resume_files()
    
    def list_available_files(self):
        """Print all available files in cache."""
        print("Available Job Descriptions:")
        print("-" * 30)
        for jd_name in sorted(self.jd_cache.keys()):
            print(f"  - {jd_name}")
        
        print(f"\nAvailable Resumes:")
        print("-" * 30)
        for resume_name in sorted(self.resume_cache.keys()):
            print(f"  - {resume_name}")
        
        stats = self.get_cache_stats()
        print(f"\nCache Statistics:")
        print(f"  - Job Descriptions: {stats['jd_count']}")
        print(f"  - Resumes: {stats['resume_count']}")
        print(f"  - Total Files: {stats['total_files']}") 