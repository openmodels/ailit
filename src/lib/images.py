import os, base64
from chatwrap import openaigpt

def textify_page(pdfpath, page, resolution):
    text = page.extract_text(extraction_mode="layout", layout_mode_space_vertically=False, layout_mode_strip_rotated=False)

    ## Process images
    imagetexts = []
    if len(page.images) < 5:
        try:
            for count, image_file_object in enumerate(page.images):
                response = get_image_description(pdfpath, image_file_object, resolution)
                if response:
                    imagetexts.append(response)
        except Exception as ex:
            print(ex)
    else:
        objs = [image_file_object for count, image_file_object in enumerate(page.images)]
        
        longest = sorted(objs, key=lambda oo: len(oo.data), reverse=True)[:5]
        try:
            for image_file_object in longest:
                response = get_image_description(pdfpath, image_file_object, resolution)
                if response:
                    imagetexts.append(response)
        except Exception as ex:
            print(ex)

    if len(imagetexts) > 0:
        image_text = "In addition, the page has the following images, as described below:\n===\n" + "\n===\n".join(imagetexts) + "\n===\n"
    else:
        image_text = ""

    return f"""===
{text}
===
{image_text}"""


def get_image_description(pdfpath, image_file_object, resolution):
    encoded = base64.b64encode(image_file_object.data).decode("utf-8")
    suffix = str(hash(encoded)) + '-' + resolution
    
    cachedescpath = pdfpath.replace('.pdf', f"-{suffix}.txt")
    if os.path.exists(cachedescpath):
        with open(cachedescpath, 'r') as fp:
            return fp.read()

    response = get_image_description_ai(encoded, resolution)
    if response:
        with open(cachedescpath, 'w') as fp:
            fp.write(response)

    return response
            
def get_image_description_ai(encoded, resolution):
    try:
        response = openaigpt.chat_response_nobudget([
            { "role": "user",
              "content": [
                  { "type": "text", "text": "Please describe this image in detail." },
                  { "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded}",
                        "detail": "low"
                    }}]}])
        
        return response
    except Exception as ex:
        print(f"Error in image extraction: {ex}")
        return None
