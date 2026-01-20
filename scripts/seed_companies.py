import boto3

# Configure your region
REGION = 'us-east-1'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table('job_scraper_companies')

# Add your companies here
COMPANIES = [
    {
        'company_name': 'Anthropic',
        'url': 'https://www.anthropic.com/careers/jobs',
        'check': 'Yes'
    },
    {
        'company_name': 'OpenAI',
        'url': 'https://openai.com/careers/search/?l=07ed9191-5bc6-421b-9883-f1ac2e276ad7%2Ce8062547-b090-4206-8f1e-7329e0014e98%2Cbbd9f7fe-aae5-476a-9108-f25aea8f6cd2%2C16c48b76-8036-4fe3-a18f-e9d357395713%2C6252b4ed-714d-469a-a970-7a13101bac9d&c=ab2b9da4-24a4-47df-8bed-1ed5a39c7036%2C86a66e6f-8ddc-493d-b71f-2f6f6d2769a6%2Ce2a6a756-466b-4b91-be68-bb0c96102de1%2C6dd4a467-446d-4093-8d57-d4633a571123%2Cd36236ec-fb74-49bd-bd3f-9d8365e2e2cb%2C18ad45e4-3e90-44b9-abc6-60b2df26b03e%2C27c9a852-c401-450e-9480-d3b507b8f64a%2C0f06f916-a404-414f-813f-6ac7ff781c61%2C3345bedf-45ec-4ae1-ad44-b0affc79bcb5%2C0c0f1511-91d1-4317-a68a-52ec2f849450%2C224d99ae-26ec-4751-8af3-ed7d104b60a2%2Cfb2b77c5-5f20-4a93-a1c4-c3d640d88e04',
        'check': 'Yes'
    },
    {
        'company_name': 'Deepmind',
        'url': 'https://job-boards.greenhouse.io/deepmind',
        'check': 'Yes' 
    },
    {
        'company_name': 'xAI',
        'url': 'https://x.ai/careers/open-roles?location=palo+alto%252C+ca,memphis%252C+tn,san+francisco%252C+ca,new+york%252C+ny,bastrop%252C+tx,los+angeles%252C+ca,washington%252C+d.c.,southaven%252C+ms,san+jose%252C+ca,seattle%252C+wa,bay+area%252C+ca,remote&dept=4024733007,4062428007,4046295007,4052172007,4046294007',
        'check': 'Yes' 
    },
    {
        'company_name': 'Jane Street',
        'url': 'https://www.janestreet.com/jobs/main.json',
        'check': 'Yes' 
    },
    {
        'company_name': 'Citadel',
        'url': 'https://www.citadel.com/careers/open-opportunities?experience-filter=experienced-professionals&sections-filter=engineering,investing,quantitative-research&location-filter=americas,chicago,greenwich,houston,miami,new-york&selected-job-sections=388,389,387,390&current_page=1&sort_order=DESC&per_page=10&action=careers_listing_filter',
        'check': 'Yes' 
    },
    {
        'company_name': 'Two Sigma',
        'url': 'https://careers.twosigma.com/careers/OpenRoles/?5086=%5B16718738%2C16718736%5D&5086_format=3149&listFilterMode=1&jobRecordsPerPage=10&jobOffset=0',
        'check': 'Yes' 
    },
    {
        'company_name': 'Point72',
        'url': 'https://careers.point72.com/?experience=experienced%20professionals&location=stamford;new%20york;chicago;san%20francisco;seattle;washington,%20dc;west%20palm%20beach%20/%20miami&area=investing;research,%20data%20%26%20analytics;technology%20%26%20engineering;trading%20%26%20transaction%20management',
        'check': 'Yes' 
    },
    {
        'company_name': 'Renaissance Technologies',
        'url': 'https://www.rentec.com/careers',
        'check': 'Yes' 
    },
    {
        'company_name': 'SSI',
        'url': 'https://jobs.ashbyhq.com/ssi/b91659e4-9352-46fa-b3c5-4fb28827eb2e',
        'check': 'No' 
    },
    {
        'company_name': 'Thinking Machines',
        'url': 'https://job-boards.greenhouse.io/thinkingmachines',
        'check': 'Yes' 
    },
    {
        'company_name': 'Perplexity',
        'url': 'https://jobs.ashbyhq.com/Perplexity/',
        'check': 'Yes' 
    },
    {
        'company_name': 'Mistral',
        'url': 'https://jobs.lever.co/mistral?commitment=Full-time',
        'check': 'Yes' 
    },
    {
        'company_name': 'Meta',
        'url': 'https://www.metacareers.com/jobsearch?offices[0]=Remote%2C%20US&offices[1]=North%20America&roles[0]=Full%20time%20employment&q=machine%20learning%20',
        'check': 'Yes' 
    },
    {
        'company_name': 'Google',
        'url': 'https://www.google.com/about/careers/applications/jobs/results/?location=United%20States&employment_type=FULL_TIME&sort_by=date&q=machine%20learning&target_level=MID',
        'check': 'Yes' 
    },
    {
        'company_name': 'Apple',
        'url': 'https://jobs.apple.com/en-us/search?location=united-states-USA&key=machine-learning',
        'check': 'Yes' 
    },
    {
        'company_name': 'Microsoft',
        'url': 'https://apply.careers.microsoft.com/careers?query=Machine+Learning&start=0&location=United+States%2C+Multiple+Locations%2C+Multiple+Locations&pid=1970393556630600&sort_by=timestamp&filter_include_remote=1&filter_employment_type=full-time&filter_profession=analytics%2Cresearch%252C%2520applied%252C%2520%2526%2520data%2520sciences%2Csoftware+engineering&filter_seniority=Mid-Level',
        'check': 'Yes' 
    },
    {
        'company_name': 'Amazon',
        'url': 'https://amazon.jobs/en/search/?offset=0&result_limit=10&sort=recent&job_type%5B%5D=Full-Time&country%5B%5D=USA&distanceType=Mi&radius=24km&industry_experience=four_to_six_years&is_manager%5B%5D=0&latitude=38.89036&longitude=-77.03196&loc_group_id=&loc_query=United%20States&base_query=machine%20learning&city=&country=USA&region=&county=&query_options=&',
        'check': 'Yes' 
    },
    {
        'company_name': 'Nvidia',
        'url': 'https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite?q=machine+learning&locationHierarchy1=2fcb99c455831013ea52fb338f2932d8&timeType=5509c0b5959810ac0029943377d47364&jobFamilyGroup=0c40f6bd1d8f10ae43ffaefd46dc7e78&jobFamilyGroup=0c40f6bd1d8f10ae43ffc8817cf47e8e&workerSubType=0c40f6bd1d8f10adf6dae161b1844a15',
        'check': 'Yes' 
    },
    {
        'company_name': 'Netflix',
        'url': 'http://explore.jobs.netflix.net/careers?query=machine%20learning&location=United%20States&pid=790303746348&domain=netflix.com&sort_by=new',
        'check': 'Yes' 
    },
    {
        'company_name': 'Reddit',
        'url': 'https://job-boards.greenhouse.io/reddit?departments%5B%5D=71092&departments%5B%5D=16253&offices%5B%5D=48028&offices%5B%5D=10769&offices%5B%5D=10168&offices%5B%5D=10167&offices%5B%5D=88237',
        'check': 'Yes' 
    },
    {
        'company_name': 'Spotify',
        'url': 'https://www.lifeatspotify.com/jobs?j=permanent&c=backend&c=data&c=developer-tools-infrastructure&c=machine-learning&c=tech-research&c=data-insights-leadership&c=data-science&c=machine-learning-data-research-insights&c=tech-research-data-research-insights&c=user-research&l=new-york&l=boston&l=miami&l=united-states-of-america-home-mix',
        'check': 'Yes' 
    },
    {
        'company_name': 'Tiktok',
        'url': 'https://lifeattiktok.com/search?job_category_id_list=6704215862603155720&keyword=machine+learning&limit=12&location_code_list=CT_1103355%2CCT_157%2CCT_94%2CCT_114%2CCT_247%2CCT_1000001%2CCT_243%2CCT_104%2CCT_75%2CCT_1103348%2CCT_233%2CCT_223%2CCT_1103554%2CCT_221&offset=0&recruitment_id_list=1&subject_id_list=',
        'check': 'Yes' 
    },
    {
        'company_name': 'Uber',
        'url': 'https://www.uber.com/us/en/careers/list/?query=machine%20learning&location=USA-California-San%20Francisco&location=USA-California-Sunnyvale&location=USA-California-Culver%20City&location=USA-New%20York-New%20York&location=USA-Illinois-Chicago&location=USA-Washington-Seattle&location=USA-Texas-Dallas&location=USA-Arizona-Phoenix&location=USA-Florida-Miami&location=USA-District%20of%20Columbia-Washington&location=USA-California-Los%20Angeles&location=USA-Massachusetts-Boston&department=Data%20Science&department=Engineering&team=Backend&team=Data&team=Data%20Scientist&team=Engineering&team=Machine%20Learning',
        'check': 'Yes' 
    },
    {
        'company_name': 'Waymo',
        'url': 'https://careers.withwaymo.com/jobs/search?block_index=0&block_uid=2ddfa6933a2443a69f97b24d1d165a22&country_codes%5B%5D=US&department_uids%5B%5D=9edee38059d1b1ce766fe8312f3bc75e&department_uids%5B%5D=451e57010e816b71a8312792faf5740f&employment_type_uids%5B%5D=2ea50d7de0fbb2247d09474fbb5ee4da&location_uids=&page=1&page_row_index=1&page_row_uid=71208e73b81e8bf96151da4f51268c9a&page_version_uid=46864c8d67c81d288123cd150b3b6972&query=machine+learning&search_cities=&search_country_codes=&search_departments=&search_dropdown_field_1_values=&search_employment_types=&search_states=&sort=',
        'check': 'Yes' 
    },
    {
        'company_name': 'FigureAI',
        'url': 'https://job-boards.greenhouse.io/figureai?page=1',
        'check': 'Yes' 
    },
    {
        'company_name': 'TogetherAI',
        'url': 'https://job-boards.greenhouse.io/togetherai?departments%5B%5D=4033058007&departments%5B%5D=4033059007&departments%5B%5D=4033061007&offices%5B%5D=4029317007&offices%5B%5D=4029318007',
        'check': 'Yes' 
    },
    {
        'company_name': 'HuggingFace',
        'url': 'https://apply.workable.com/huggingface/',
        'check': 'Yes' 
    },
    {
        'company_name': 'Cohere',
        'url': 'https://jobs.ashbyhq.com/cohere?employmentType=FullTime',
        'check': 'Yes' 
    },
    {
        'company_name': 'Reflection AI',
        'url': 'https://jobs.ashbyhq.com/reflectionai',
        'check': 'Yes' 
    },
    {
        'company_name': 'Jump',
        'url': 'https://www-webflow.jumptrading.com/hr/experienced-candidates',
        'check': 'Yes' 
    },
    {
        'company_name': 'HRT',
        'url': 'https://www.hudsonrivertrading.com/careers/?locations=austin%2Cbellevue%2Cboulder%2Ccarteret%2Cchicago%2Cnew-york%2Cseattle%2C&job-type=full-time-experienced%2Cparent_full-time-experienced%2C&job-category=software-engineeringc%2Cparent_software-engineeringc%2Csoftware-engineeringpython%2Cstrategy-development%2C',
        'check': 'Yes' 
    },
    {
        'company_name': 'IMC',
        'url': 'https://www.imc.com/us/search-careers?jobDepartments=Technology%2CTrading&jobOffices=Chicago%2CNew+York%2CRemote+-+US&jobTypes=Experienced&page=1',
        'check': 'Yes' 
    },
    {
        'company_name': 'DRW',
        'url': 'https://www.drw.com/work-at-drw/listings?filterType=country&value=United+States',
        'check': 'Yes' 
    },
    {
        'company_name': 'Tower',
        'url': 'https://tower-research.com/roles/',
        'check': 'Yes' 
    },
    {
        'company_name': 'Optiver',
        'url': 'https://optiver.com/working-at-optiver/career-opportunities/',
        'check': 'Yes' 
    },
    {
        'company_name': 'DE Shaw',
        'url': 'https://www.deshaw.com/careers/choose-your-path',
        'check': 'Yes' 
    },
    {
        'company_name': 'XTX',
        'url': 'https://api.xtxcareers.com/jobs.json',
        'check': 'Yes' 
    },
]

def seed_companies():
    """Seed the companies table with initial data"""
    for company in COMPANIES:
        table.put_item(Item=company)
        print(f"✅ Added: {company['company_name']}")

if __name__ == '__main__':
    print("Seeding companies...")
    seed_companies()
    print("Done!")