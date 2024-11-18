import pymongo
from bs4 import BeautifulSoup
import re

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['web_crawler']
pages_collection = db['pages']
professors_collection = db['professors']

def extract_faculty_info(faculty_div):
    
    if not faculty_div or not faculty_div.get_text(strip=True):
        return None 
    faculty_data = {}

    """
    <div class="clearfix">
        <img alt="Abdelfattah Amamra" height="161" src="../img/faculty-staff/abdel.jpg" style="width: 150px; height: auto; margin-right: 8px; float: left;" width="120"/>
        <h2>Abdelfattah Amamra</h2>
        <p>
            <strong>Title:</strong>Associate Professor <br/> 
            <strong>Office:</strong> 8-11 <br/> 
            <strong>Phone:</strong> (909) 869-3447 <br/> 
            <strong>Email: </strong> <a href="mailto:aamamra@cpp.edu">aamamra@cpp.edu</a> <br/> 
            <strong>Web:</strong> <a href="https://www.cpp.edu/faculty/aamamra/index.shtml">cpp.edu/faculty/aamamra/</a></p>
    </div>
    """

    name_tag = faculty_div.find('h2')
    faculty_data['name'] = name_tag.get_text(strip=True) if name_tag else 'N/A'

    p_tag = faculty_div.find('p') 
    title_match = re.search(r'Title\s*(.*?)(?=\s*<br|$)', str(p_tag))
    x = title_match.group(0).strip()
    x = re.sub(r'[^\x00-\x7F]+', ' ', x)
    faculty_data['title'] = x.split(' ', 1)[1] if x else 'N/A'

    office_match = re.search(r'Office\s*(.*?)(?=\s*<br|$)', str(p_tag))
    x = office_match.group(0).strip()
    x = re.sub(r'[^\x00-\x7F]+', ' ', x)
    faculty_data['office'] = x.split(' ', 1)[1] if x else 'N/A'

    phone_match = re.search(r'Phone\s*(.*?)(?=\s*<br|$)', str(p_tag))
    x = phone_match.group(0).strip()
    x = re.sub(r'[^\x00-\x7F]+', ' ', x)
    faculty_data['phone'] = x.split(' ', 1)[1] if x else 'N/A'
    

    email_tag = faculty_div.find('a', href=re.compile(r'mailto:.*'))
    if email_tag:
        faculty_data['email'] = email_tag['href'].replace('mailto:', '').strip()
    else:
        faculty_data['email'] = 'N/A'

    website_tag = None
    all_a_tags = faculty_div.find_all('a', href=True)
    if len(all_a_tags) > 1:
        website_tag = all_a_tags[1]
    if website_tag and website_tag['href'].startswith('http'):
        faculty_data['website'] = website_tag['href'].strip()
    else:
        faculty_data['website'] = 'N/A'

    print(faculty_data)
    return faculty_data

def parse_faculty_page(html):

    soup = BeautifulSoup(html, 'html.parser')
    faculty_list = []

    faculty_divs = soup.find_all('div', class_='clearfix')
    
    for faculty_div in faculty_divs:
        faculty_data = extract_faculty_info(faculty_div)
        faculty_list.append(faculty_data)

    return faculty_list


def main():
    target_url = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"
    page = pages_collection.find_one({'url': target_url})
    html = page['html']
    faculty_list = parse_faculty_page(html)
    #professors_collection.insert_many(faculty_list)
    for faculty_data in faculty_list:
        if faculty_data is not None:
            professors_collection.insert_one(faculty_data)

if __name__ == "__main__":
    main()
