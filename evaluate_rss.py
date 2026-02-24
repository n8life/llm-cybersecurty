import feedparser
import json
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

# Replace with your OpenAI API key
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"

def analyze_feed(feed_url):
    """
    Parses an RSS feed, analyzes each entry, and returns a JSON list of analyzed items.
    """
    feed = feedparser.parse(feed_url)
    entries = feed.entries

    analyzed_items = []

    for entry in entries:
        title = entry.title
        summary = entry.summary
        #Sometimes there is no summary.  Handle that.
        if summary is None:
            summary = ""

        analysis = analyze_entry(title, summary)
        analyzed_items.append(analysis)

    return json.dumps(analyzed_items, indent=2)


def analyze_entry(title, summary):
    """
    Analyzes a single feed entry using a Langchain LLM.
    """

    # Prompt Template
    prompt_template = """
    You are a cybersecurity analyst tasked with classifying RSS feed entries. 
    Based on the following title and summary, determine:
    1. Is this a security advisory/threat intelligence report, or an advertisement?  
    Answer with only "Security Advisory/Threat Intelligence Report" or "Advertisement".
    2. If it's a Security Advisory, what security framework(s) would this information be relevant to? (e.g. MITRE ATT&CK, NIST, ISO 27001)
    3. What level of technical language is used? (e.g. Highly technical, Technical, Accessible to IT professionals)
    4. If applicable, what platform(s) does this threat target? (e.g. WordPress, Windows, Linux, Android, iOS, Cloud)
    5. Summarize the key information in 1-2 sentences.

    Here's the title: {title}
    Here's the summary: {summary}

    Output in JSON format with the following keys: "title", "type", "framework", "language", "platform", "summary".  Do not include any preamble or explanation.
    """

    prompt = PromptTemplate(template=prompt_template, input_variables=["title", "summary"])
    llm = OpenAI(temperature=0.2)  #Adjust temperature for more/less creativity
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.run(title=title, summary=summary)

    try:
        #Attempt to parse as JSON.  LLM responses can be imperfect, so handle errors.
        analysis = json.loads(response)
        return analysis
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Problematic Response: {response}") #Print the response to help debug.
        #Return a default dictionary to avoid crashing.  You might want to log this event.
        return {
            "title": title,
            "type": "Unknown",
            "framework": "Unknown",
            "language": "Unknown",
            "platform": "Unknown",
            "summary": "Unable to parse response from LLM."
        }



if __name__ == "__main__":
    feed_url = "https://cybersecuritynews.com/feed/"
    analysis_results = analyze_feed(feed_url)
    print(analysis_results)
