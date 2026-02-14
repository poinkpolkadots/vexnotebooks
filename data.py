import lmstudio, fitz, os, shutil

def pdf_to_images(path): #convert each page of a PDF to an image and return list of images
    doc = fitz.open(path) #open the PDF document
    paths = []

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
        paths.append(ipath) #add image path to list
    doc.close() #close the PDF document

    return [lmstudio.prepare_image(path) for path in paths] #return list of images

def pdf_to_text(path): #convert PDF to text
    doc = fitz.open(path) #open the PDF document
    text = ""
    for page_num in range(len(doc)): #iterate through each page
        page = doc.load_page(page_num) #load the page
        text += f"\npage {page_num + 1}\n" + page.get_text() #extract text and add to string
    doc.close() #close the PDF document
    return text #return the extracted text

def summarize_image_pdf_pages(pdf_path): #main function to summarize each page of a PDF given the path to the PDF
    intepret = lmstudio.llm("zai-org/glm-4.6v-flash") #model for interpreting images TODO: use a faster model pls
    page_summaries = [] #list to hold summaries of each page
    for i, image in enumerate(pdf_to_images(pdf_path)): #iterate through each page image in the pdf
        pagechat = lmstudio.Chat.from_history({"messages": [ #TODO: figure out system and user prompts
            { "role": "system", "content": (
                "You are a VEX Robotics Judge's Assistant. Your task is to extract evidence from notebook pages based on the 2025 REC Foundation Rubric."
                "Give a quick and detailed summary; do not reason, just extract evidence. Focus on extracting evidence that relates to the rubric criteria, "
                "do not worry about formatting or organization of the evidence, just extract as much relevant evidence as you can."
            )}, { "role": "user", "content": (
                "Extract all evidence on this page that relates to the Engineering Notebook Rubric criteria."
            ), "images": [image]}
        ]})

        res = intepret.respond(pagechat, config={ "temperature": 0.0 }).content #get summary for each page without any DREAMING
        page_summaries.append(res) #add summary to list
        print(res) #TODO: THIS IS DEBUG, REMOVE LATER
    
    return page_summaries #return list of page summaries

#model = lmstudio.llm("llama-3.2-3b-instruct")
#for fragment in model.respond_stream(lmstudio.Chat.from_history({"messages": [ #chat for summaries
#    { "role": "system", "content": (
#        'You are acting as an assistant to VEX Robotics Judges. '
#        'You will generate resources for them to help them in grading engineering notebooks. Write in a way such that a highschooler would understand what you are saying.'
#        'Do not grade or rank the notebooks, act only as an assistant, generating questions to help the actual judges with evaluating and grading notebooks.'
#    )}, { "role": "user", "content": (
#        "Given the following notebook, generate a list of questions that a judge should ask themselves when evaluating the notebook. "
#        "The questions should be based on the 2025 REC Foundation Rubric criteria, and should help the judge evaluate the notebook based on the evidence provided in the summaries. "
#        "The questions should be general enough to apply to any notebook, but specific enough to be helpful in evaluating the notebook based on the evidence provided."
#        "Here is the notebook in text form, understand that there were images left out:\n" + 
#        pdf_to_text("C:/Users/lawre/OneDrive/Documents/vex/vexnotebooks/HTML_Site/pdfs/Sample2-Engineering-notebook.pdf")
#    )}
#]})):
#    print(fragment.content, end="", flush=True)
#print()