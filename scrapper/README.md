#Scrapper

This python3 scripts generates a key/value (URL/hash) CSV file from a list of links to scrap.

#Installation

pip3 install -r requirements.txt

#Usage

First, uncomment/comment the links you want to scrap in the 'links.txt' file.

python3 scrapper.py

#Base Links Notes

- The 'links.txt' file contains the base URLs to scrap, URLs starting with '#' will be ignored.

- To add a GitHub repository you have to do as the following : 

  - Get the repository URL and extract the "author/repo" pair, for example :
    https://github.com/Storm75/HacknowledgeTools        -> Storm75/HacknowledgeTools

  - Then insert it in the following URL format :
    https://api.github.com/repos/{AUTHOR/REPONAME}/tags -> https://api.github.com/repos/Storm75/HacknowledgeTools/tags

#Download Notes
- If you find files that the scrapper ignores, check that his extension is contained into the EXTS variable 'EXTS = ('.zip', '.gz', '.tgz', '.bz2', '.xz', '.dmg')'

- In the download step, if some file sizes show "0B" (happens a lot with GitHub), it means the server doesn't send the Content-Length HTTP header, but the file is still correctly downloaded.

- Only files which the URL isn't already in the hash_list.csv will be downloaded, otherwise they are skipped.

