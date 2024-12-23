import os


cm_to_in = 1/2.54  # centimeters to inches
m_to_cm = 100  # meters to centimeters
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LATEX_TEMPLATES_DIR = os.path.join(BASE_DIR, 'src', 'pdf_generator')
TEMP_DIR = os.path.join(BASE_DIR, 'data', 'temp')
PDFS_DIR = os.path.join(BASE_DIR, 'data', 'pdfs')
RESULTS_DIR = os.path.join(BASE_DIR, 'data', 'results')
ANNOTATION_DISPLACEMENT_MINIMUM = 0.01  # meters
ANNOTATION_THRESHOLD = 0.01  #
