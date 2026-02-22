# A release note agent 
Create a release note agent , which automatically creates release notes as defects are resolved by dev engineers 
This is greenfield implementation for experimentation and not a go live production agent.

## Tools 
### Release note generation agent
This would be a agentic program 
Agent has to be written using claude code agent SDK (claude_agent_sdk)

It needs to be a conversational agent . ClaudeSDKClient should be used.
User would initiate the agent and when the time comes for software release .
User would prompt the label for which release notes needs to be created.
user might ask to shutdown the agent or lock the release notes from further change.
Use well knowm mcp servers and skills whenever possible.

### Logic
which would be polling defects table .
Defects which are resolved by code fixes are to be considered . defect status == 'RESOLVED' . Other statuses would not be present in the release notes table
create a nice word document with a table and 4 columns 
  * Defect id 
  * Defect title 
  * Defect date 
  * Developer comment
  * Defect label 

If particular defect if it was earlier resolved and then a QA reverts status to "OPEN" , then this defect needs to be removed from table .


### Database for defects 
we will use sqlite database
* Defects will be stored in defects table 
* Release build no will be stored in release_info table.


### User interface 
User interface would be pure html . 
User can create and update defects and the defects will get updated in sqllite database.

