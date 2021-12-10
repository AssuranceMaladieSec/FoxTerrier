# Installation

```
git clone https://github.com/AssuranceMaladieSec/FoxTerrier
pip install neo4j
```

# Usage

To Use FoxTerrier, The Neo4j **database must be up and running and already filled with the SharpHound data**. 

When your `conf.ini` and `template.json` are ready, You just have to launch the script !

```
python FoxTerrier.py
```

# Configuration files
## input file : `template.json` :

`template.json` contains the data used by FoxTerrier to create the specific Cypher Queries. 

In this file 6 parameters can be used:
- **node_start_type**	: <span style="color:red">*Mandatory*</span>. Must be `"User"` or `"Group"`.
- **node_start_name**	: <span style="color:red">*Mandatory*</span>. Can be the full name or a regex (cf.`is_node_start_regex`). Example `"JOHN-DOE-825@MYDOMAIN.LOCAL"` or `"JOHN-DOE-\\d{3}@MYDOMAIN.LOCAL"`.
- **is_node_start_regex** : If regex are used in `node_start_name`, the value must be `true` (be careful to use the value `true` and not the string `"true"`). *Default value : **false***
- **mode** : Relation between start node and objects can be direct or indirect (permissions inherited from a group membership). You can set the mode of your choice by choising between the value `"direct"`, `"indirect"` or `"all"` (`all` is "direct"+"indirect"). *Default value : **"direct"***
 - **objects_type** : The target objects can be `"GPO"`, `"OU"`, `"User"`, `"Group"`,`"RDP"`. **The values must be within a list**. *Default value : **["GPO", "OU" ,"User", "Group", "RDP"]***
- **exclude_node** : When using regex the results can be overwhelming. It's possible to exclude specific nodes from the queries. **The values must be within a list**. Example : `["GENERIC-GROUP-11111111@MONDOMAIN.LOCAL","GENERIC-GROUP-22222222@MONDOMAIN.LOCAL"]`

Here is an example of a `template.json` file:

 ```
 {	
	"queries": 
	[	
		{
			"node_start_type": "Group",
 			"node_start_name": "GENERIC-GROUP-\\d{8}.*@MYDOMAIN.LOCAL",
			"is_node_start_regex": true,
			"mode": "all",
			"objects_type": ["GPO", "OU" ,"User", "Group","RDP"],
			"exclude_node": ["GENERIC-GROUP-11111111@MYDOMAIN.LOCAL","GENERIC-GROUP-22222222@MYDOMAIN.LOCAL"]
		},
		{
			"node_start_type": "User",
			"node_start_name": "MY-AD-ACCOUNT@MYDOMAIN.LOCAL",
			"is_node_start_regex": false,
			"mode": "direct",
			"objects_type": ["GPO"],
		}		
	]
 }
 ```
 
## Configuration file : `conf.ini`

The file `conf.ini` contains the neo4j credentials, the file name of the summary and the report and the template file name. If you want to change the name of the file generated or the input file, it's here.

 ```
[neo4j_credentials]
username=PutYourNeo4jLoginHere
password=PutYourNeo4jPasswordHere
address=127.0.0.1
port=7687

[files]
template_file=template.json
csv_report=my_report.csv
txt_summary=my_summary.txt
 ```

# FoxTerrier presentation

<img align="right" height="260" src="https://i.ibb.co/VvZShyt/TF.png">

FoxTerrier is a Free Software tool written in Python and ***working in the BloodHound environment***.

> FoxTerrier can be seen as a **more flexible version without GUI of BloodHound `OUTBOUND CONTROL RIGHTS` and `EXECUTION RIGHTS (RDP only)` features**. 
> 
> In addition, FoxTerrier provides **all the results in a `csv` file and a `.txt` summary of it**.

FoxTerrier allows you to :

* **set multiple starting points**: identify, from a predefined list of user/groups, all the vulnerable objects (GPO, OU, User, Group, machine with RDP connection available for the object) that can be compromised by them.
* **set the type of the desired vulnerable objects**: unlike the BloodHound `OUTBOUND CONTROL RIGHTS` feature, FoxTerrier allows you to narrow down your requests on specific objects types. 
  For instance, if you want to retrieve only the vulnerable GPO that can be compromised by a list of predefined users/groups, you can :)
* **use regexp**: predefined users and groups can be expressed as regular expressions. It can be handy, for instance, if you want to target, in your `start node`, all users/groups matching a specific pattern.

> **Prerequisite:** FoxTerrier relies on the Neo4j databases already filled with Active Directory information provided by SharpHound.

# Output examples

# A `summary.txt` example : 

```
--- Load JSON File C:\Users\XXX\Documents\Tool\FoxTerrier\template.json
--- JSON file C:\Users\XXX\Documents\Tool\FoxTerrier\template.json Loaded ---

--- Executed queries ---

Match p=(m:Group)-[r]->(n:GPO) WHERE m.name =~ 'MONGROUPE_GENERIQUE-\d{11}.*@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-11111111111@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-22222222222@MONDOMAIN.LOCAL' and r.isacl=true return m.name AS start_name, n.name AS end_name

Match p=(m:Group)-[r1:MemberOf*1..]->(g2:Group)-[r2]->(n:GPO) WHERE m.name =~ 'MONGROUPE_GENERIQUE-\d{11}.*@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-11111111111@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-22222222222@MONDOMAIN.LOCAL' and r2.isacl=true return m.name AS start_name, n.name AS end_name

Match p=(m:Group)-[r]->(n:OU) WHERE m.name =~ 'MONGROUPE_GENERIQUE-\d{11}.*@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-11111111111@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-22222222222@MONDOMAIN.LOCAL' and r.isacl=true return m.name AS start_name, n.name AS end_name

Match p=(m:Group)-[r1:MemberOf*1..]->(g2:Group)-[r2]->(n:OU) WHERE m.name =~ 'MONGROUPE_GENERIQUE-\d{11}.*@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-11111111111@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-22222222222@MONDOMAIN.LOCAL' and r2.isacl=true return m.name AS start_name, n.name AS end_name

Match p=(m:Group)-[r]->(n:User) WHERE m.name =~ 'MONGROUPE_GENERIQUE-\d{11}.*@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-11111111111@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-22222222222@MONDOMAIN.LOCAL' and r.isacl=true return m.name AS start_name, n.name AS end_name

Match p=(m:Group)-[r1:MemberOf*1..]->(g2:Group)-[r2]->(n:User) WHERE m.name =~ 'MONGROUPE_GENERIQUE-\d{11}.*@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-11111111111@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-22222222222@MONDOMAIN.LOCAL' and r2.isacl=true return m.name AS start_name, n.name AS end_name

Match p=(m:Group)-[r]->(n:Group) WHERE m.name =~ 'MONGROUPE_GENERIQUE-\d{11}.*@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-11111111111@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-22222222222@MONDOMAIN.LOCAL' and r.isacl=true return m.name AS start_name, n.name AS end_name

Match p=(m:Group)-[r1:MemberOf*1..]->(g2:Group)-[r2]->(n:Group) WHERE m.name =~ 'MONGROUPE_GENERIQUE-\d{11}.*@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-11111111111@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-22222222222@MONDOMAIN.LOCAL' and r2.isacl=true return m.name AS start_name, n.name AS end_name

Match p=(m:Group)-[r:CanRDP]->(n:Computer) WHERE m.name =~ 'MONGROUPE_GENERIQUE-\d{11}.*@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-11111111111@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-22222222222@MONDOMAIN.LOCAL' return m.name AS start_name, n.name AS end_name

Match p=(m:Group)-[r1:MemberOf*1..]->(g2:Group)-[r2:CanRDP]->(n:Computer) WHERE m.name =~ 'MONGROUPE_GENERIQUE-\d{11}.*@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-11111111111@MONDOMAIN.LOCAL' AND NOT m.name = 'MONGROUPE_GENERIQUE-22222222222@MONDOMAIN.LOCAL' return m.name AS start_name, n.name AS end_name

--- Summary of vulnerable object per User or Group ---

MONGROUPE_GENERIQUE-33333333333@MONDOMAIN.LOCAL : 1
MONGROUPE_GENERIQUE-66666666666@MONDOMAIN.LOCAL : 1
MONGROUPE_GENERIQUE-99999999999@MONDOMAIN.LOCAL : 1
MONGROUPE_GENERIQUE-00000000000@MONDOMAIN.LOCAL : 1
MONGROUPE_GENERIQUE-77777777777@MONDOMAIN.LOCAL : 1
MONGROUPE_GENERIQUE-44444444444@MONDOMAIN.LOCAL : 2

--- Summary of CanRDP machines per User or Group ---

MONGROUPE_GENERIQUE-33333333333@MONDOMAIN.LOCAL : 3289
MONGROUPE_GENERIQUE-66666666666@MONDOMAIN.LOCAL : 521
MONGROUPE_GENERIQUE-99999999999@MONDOMAIN.LOCAL : 141
MONGROUPE_GENERIQUE-00000000000@MONDOMAIN.LOCAL : 35
MONGROUPE_GENERIQUE-77777777777@MONDOMAIN.LOCAL : 5
MONGROUPE_GENERIQUE-44444444444@MONDOMAIN.LOCAL : 84
MONGROUPE_GENERIQUE-33333333366@MONDOMAIN.LOCAL : 300
MONGROUPE_GENERIQUE-99333333366-RED@MONDOMAIN.LOCAL : 459
MONGROUPE_GENERIQUE-55444444444@MONDOMAIN.LOCAL : 459
MONGROUPE_GENERIQUE-82333333366@MONDOMAIN.LOCAL : 697

--- Summary of vulnerable object per Type ---

GPO : 4
OU : 1
User : 1
Group : 1
CanRDP : 5990

--- Results available in My_Report.csv ---
```

# A `report.csv` example:

The results are displayed here in a table for presentation purpose. The results are stored in a csv format in the report file.

| Start Object 				| Vulnerable Object 				|Distinguished Name Vulnerable Object 													| Type |
| -----------  				| 	----------- 					| ----------- 																			|  -----------  |
| MY-USER@MONDOMAIN.LOCAL 	| GPO-169519@MONDOMAIN.LOCAL  		|CN={12345678-1234-5678-9123-012345678944},CN=Policies,CN=System,DC=mondomain,DC=local	| GPO 			|
| MY-USER@MONDOMAIN.LOCAL 	| GPO-1881@MONDOMAIN.LOCAL 			|CN={12345678-1234-5678-9123-012345678955},CN=Policies,CN=System,DC=mondomain,DC=local	| GPO 			|
| MY-USER@MONDOMAIN.LOCAL 	| GPO-94984@MONDOMAIN.LOCAL 		|CN={12345678-1234-5678-9123-012345678977},CN=Policies,CN=System,DC=mondomain,DC=local	| GPO 			|
| MY-USER@MONDOMAIN.LOCAL 	| Berlin@MONDOMAIN.LOCAL  			|OU=Berlin,OU=Germany,OU=My Big Company,DC=mondomain,DC=local							| OU 			|
| MY-USER@MONDOMAIN.LOCAL 	| GPO-71188@MONDOMAIN.LOCAL  		|CN={12345678-1234-5678-9123-012345678966},CN=Policies,CN=System,DC=mondomain,DC=local	| GPO 			|
| MY-USER@MONDOMAIN.LOCAL 	| GPO-72618@MONDOMAIN.LOCAL  		|CN={12345678-1234-5678-9123-012345678922},CN=Policies,CN=System,DC=mondomain,DC=local	| GPO 			|
| MY-USER@MONDOMAIN.LOCAL 	| New-York@MONDOMAIN.LOCAL 			|OU=New-York,OU=USA,OU=My Big Company,DC=mondomain,DC=local								| OU 			|
| MY-USER@MONDOMAIN.LOCAL 	| GPO-4514@MONDOMAIN.LOCAL  		|CN={12345678-1234-5678-9123-012345678999},CN=Policies,CN=System,DC=mondomain,DC=local	| GPO 			|
| MY-USER@MONDOMAIN.LOCAL 	| GPO-72967@MONDOMAIN.LOCAL  		|CN={12345678-1234-5678-9123-012345678933},CN=Policies,CN=System,DC=mondomain,DC=local	| GPO 			|
| MY-USER@MONDOMAIN.LOCAL 	| GROUP-1644@MONDOMAIN.LOCAL  		|CN=GROUP-1644,OU=Berlin,OU=Germany,OU=My Big Company,DC=mondomain,DC=local				| Group 			|
| MY-USER@MONDOMAIN.LOCAL 	| GPO-2561@MONDOMAIN.LOCAL 			|CN={12345678-1234-5678-9123-012345678911},CN=Policies,CN=System,DC=mondomain,DC=local	| GPO 			|

