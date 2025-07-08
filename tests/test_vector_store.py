import unittest
import os
from unittest.mock import patch, MagicMock
from utils.vector_store import setup_vector_store, FAISS_INDEX_PATH

class TestVectorStore(unittest.TestCase):

    @patch('utils.vector_store.BedrockEmbeddings')
    @patch('utils.vector_store.FAISS')
    @patch('os.path.exists')
    def test_setup_vector_store_loads_existing(self, mock_exists, mock_faiss, mock_embeddings):
        """Test loading an existing vector store."""
        mock_exists.return_value = True
        mock_faiss_instance = MagicMock()
        mock_faiss.load_local.return_value = mock_faiss_instance

        vector_store = setup_vector_store("any_dir")

        mock_exists.assert_called_once_with(FAISS_INDEX_PATH)
        mock_faiss.load_local.assert_called_once()
        self.assertEqual(vector_store, mock_faiss_instance)

    @patch('utils.vector_store.BedrockEmbeddings')
    @patch('utils.vector_store.FAISS')
    @patch('utils.vector_store.DirectoryLoader')
    @patch('utils.vector_store.RecursiveCharacterTextSplitter')
    @patch('os.path.exists')
    def test_setup_vector_store_creates_new(self, mock_exists, mock_splitter, mock_loader, mock_faiss, mock_embeddings):
        """Test creating a new vector store from documents."""
        # First call to os.path.exists is for FAISS_INDEX_PATH (False)
        # Second call is for docs_dir (True)
        mock_exists.side_effect = [False, True]

        # Mock document loading
        mock_txt_loader_instance = MagicMock()
        mock_pdf_loader_instance = MagicMock()
        mock_txt_loader_instance.load.return_value = [MagicMock()] # 1 doc
        mock_pdf_loader_instance.load.return_value = [MagicMock()] # 1 doc
        mock_loader.side_effect = [mock_txt_loader_instance, mock_pdf_loader_instance]

        # Mock text splitting
        mock_splitter_instance = MagicMock()
        mock_splitter_instance.split_documents.return_value = [MagicMock(), MagicMock()] # 2 chunks
        mock_splitter.return_value = mock_splitter_instance

        # Mock FAISS creation
        mock_faiss_instance = MagicMock()
        mock_faiss.from_documents.return_value = mock_faiss_instance

        vector_store = setup_vector_store("docs_dir")

        # Verify FAISS was created and saved
        mock_faiss.from_documents.assert_called_once()
        mock_faiss_instance.save_local.assert_called_once_with(FAISS_INDEX_PATH)
        self.assertEqual(vector_store, mock_faiss_instance)

    @patch('utils.vector_store.BedrockEmbeddings')
    @patch('os.path.exists', return_value=False)
    @patch('os.makedirs')
    def test_setup_vector_store_no_docs_dir(self, mock_makedirs, mock_exists, mock_embeddings):
        """Test behavior when the document directory does not exist."""
        # os.path.exists for FAISS index and docs_dir both return False
        mock_exists.side_effect = [False, False]
        vector_store = setup_vector_store("non_existent_dir")
        mock_makedirs.assert_called_once_with("non_existent_dir", exist_ok=True)
        self.assertIsNone(vector_store)

if __name__ == '__main__':
    unittest.main()