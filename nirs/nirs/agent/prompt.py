PROMPT_TEMPLATE = """
You are a network security engineer. Your task is to write a single iptables rule to block malicious traffic while allowing benign traffic, Then evaluate it using evaluate_rule tool. 

Output exactly one iptables DROP rule to append to the FORWARD table, enclosed within <rule></rule> tags. Do not produce multiple rules. Keep your response short.

IMPORTANT:
- Never block the subnet 59.166.0.0/24 and 149.171.126.0/24, even if they appear in the malicious flows above.
- If you find no safe DROP rule to generate (e.g., all malicious flows are from 59.166.0.0/24 or 149.171.126.0/24), output:
  <rule>none</rule>
- Prefer blocking entire source IPs or subnets rather than specifying protocols, ports, or destination ports unless absolutely necessary.

Valid formats include:
-A FORWARD -s <src_ip>/<subnet> -j DROP
-A FORWARD -d <dst_ip>/<subnet> -j DROP
-A FORWARD -d <dst_ip>/<subnet> -p <protocol> -j DROP
-A FORWARD -d <dst_ip>/<subnet> -p <protocol> --dport <dst_port> -j DROP

Malicious flows:
{malicious_csv}

Benign flows:
{benign_csv}
"""

# NOTE: Few-shot prompt for Mistral (did not yield particularly good results)
PROMPT_TEMPLATE_MISTRAL = """
You are a network security engineer. You must output ONE valid iptables DROP rule.
 
Your answer MUST follow ALL rules below:
 
FORMAT RULES (STRICT):
Output must be enclosed inside <rule> and </rule> tags.
The content inside must be EXACTLY ONE iptables command.
Valid syntax patterns (use ONE of these only):
-A FORWARD -s <src_ip>[/<cidr>] -j DROP
-A FORWARD -d <dst_ip>[/<cidr>] -j DROP
-A FORWARD -d <dst_ip>[/<cidr>] -p <protocol> -j DROP
-A FORWARD -d <dst_ip>[/<cidr>] -p <protocol> --dport <port> -j DROP
All fields must exist: table=FORWARD, jump=DROP, hyphens correct, CIDR required.
 
BEHAVIOR RULES:
1. Never block traffic to or from ANY IP in {critical_subnets}.
2. Block something that appears ONLY in malicious flows OR appears much more in malicious than benign.
3. Prefer the most general safe rule (bigger subnet > single IP > protocol+port).
4. The rule must NOT match any benign flow if avoidable.
5. If NO safe rule can be created, output exactly: <rule>none</rule>
 
IMPORTANT:
Do NOT create multiple rules.
Use <rule></rule> tags.
 
DATA:
Malicious flows:
{malicious_csv}
 
Benign flows:
{benign_csv}
 
EXAMPLES (Follow this pattern)
 
Example 1:
Malicious flows:
src_ip,dst_ip,protocol,src_port,dst_port,src_data,dst_data
10.0.2.5,59.166.0.8,tcp,11123,80,500,900
 
Benign flows:
src_ip,dst_ip,protocol,src_port,dst_port,src_data,dst_data
192.168.0.5,59.166.0.8,tcp,11432,80,400,500
 
<rule>-A FORWARD -s 10.0.2.5 -j DROP</rule>
 
---
 
Example 2:
Malicious flows:
src_ip,dst_ip,protocol,src_port,dst_port,src_data,dst_data
59.166.0.6,10.0.0.1,tcp,11123,22,1000,1000
 
Benign flows:
src_ip,dst_ip,protocol,src_port,dst_port,src_data,dst_data
55.1.1.11,10.0.0.2,tcp,11123,22,800,900
 
(59.166.0.0/24 is a critical subnet)
<rule>none</rule>
 
---
 
Example 3:
Malicious flows:
src_ip,dst_ip,protocol,src_port,dst_port,src_data,dst_data
172.24.5.10,10.0.2.9,udp,11123,53,200,300
 
Benign flows:
src_ip,dst_ip,protocol,src_port,dst_port,src_data,dst_data
172.24.5.8,10.0.2.9,tcp,11123,80,350,350
 
<rule>-A FORWARD -d 10.0.2.0/24 -p udp --dport 53 -j DROP</rule>

REAL DATA
 
Malicious samples:
{malicious_csv}
 
Benign samples:
{benign_csv}

Provide a rule.
"""

