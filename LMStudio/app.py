import lmstudio as lms
import fitz
import os
import shutil

mainchat = lms.Chat.from_history({"messages": [ #chat for summaries
    { "role": "system", "content": (
        'You are acting as an assistant to VEX Robotics Judges. '
        'You will generate resources for them to help them in grading engineering notebooks. Write in a way such that a highschooler would understand what you are saying.'
        'Do not grade or rank the notebooks, act only as an assistant, generating questions to help the actual judges with evaluating and grading notebooks.'
    )}
]})

def pdf_to_images(path): #convert each page of a PDF to an image and return list of image paths
    doc = fitz.open(path) #open the PDF document
    pages = []

    #create temporary directory for images
    tdir = "tdir"
    if os.path.exists(tdir):
        shutil.rmtree(tdir)
    os.makedirs(tdir)

    for page_num in range(len(doc)): #iterate through each page
        page = doc.load_page(page_num) #load the page
        pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2)) #render page to an image
        ipath = os.path.join(tdir, f"page_{page_num}.jpg") #create image path
        pix.save(ipath) #save the image to the path
        pages.append(ipath) #add image path to list
    doc.close() #close the PDF document
    return pages #return list of image paths

def pdf_to_text(path): #convert PDF to text
    doc = fitz.open(path) #open the PDF document
    text = ""
    for page_num in range(len(doc)): #iterate through each page
        page = doc.load_page(page_num) #load the page
        text += f"\npage {page_num + 1}\n" + page.get_text() #extract text and add to string
    doc.close() #close the PDF document
    return text #return the extracted text

def summarize_image_pdf_pages(pdf_path): #main function to summarize each page of a PDF given the path to the PDF
    intepret = lms.llm("qwen2.5-vl-3b-instruct") #model for interpreting images
    page_summaries = [] #list to hold summaries of each page
    for i, path in enumerate(pdf_to_images(pdf_path)): #iterate through each page image in the pdf
        pagechat = lms.Chat.from_history({"messages": [ #TODO: figure out system and user prompts
            { "role": "system", "content": (
                ""
            )}, { "role": "user", "content": "", "images": [lms.prepare_image(path)]}
        ]})

        res = intepret.respond(pagechat, config={ "temperature": 0.1 }) #get summary for each page without any DREAMING
        page_summaries.append(res) #add summary to list
    
    return page_summaries #return list of page summaries

print(pdf_to_text("C:/Users/lawre/OneDrive/Documents/vex/vexnotebooks/HTML_Site/pdfs/Sample2-Engineering-notebook.pdf")) #test pdf to text function

#TODO: do something with this (supposed to print the result of the main chat once I feed it the page summaries)
#for fragment in model.respond_stream(chat):
#    print(fragment.content, end="", flush=True)
#print()