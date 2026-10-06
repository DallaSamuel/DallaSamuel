# Hi, I'm Dalla Samuel (CyberJKD) | Azure & Cloud Operations

Junior Azure and cloud engineer with a B.Sc. in Cybersecurity, building hands-on labs in **Azure, Terraform, Active Directory, and Splunk**. Every lab is documented in public with the commands, failures, and fixes.

I work remotely on US Central hours. **Looking for:** Junior Azure / Cloud Operations roles, also Windows systems admin and IT support.

---

## 🗂️ Terraform on Azure

### 🔗 [Terraform Active Directory Domain Controller](https://github.com/DallaSamuel/CyberJKD-Labs/tree/main/phase-06/cloud-tech-techniques/cloud-system-admin-accelerator)

Provisioned an Azure network and a Windows Server 2022 domain controller in a **single `terraform apply`** (9 resources), then ran a clean `terraform destroy` with zero leftover cost. Worked through real failures: SKU capacity, quota, state drift, and a Gen1/Gen2 image mismatch.

**Skills:** Terraform (HCL), Azure VNet/NSG/NIC, Custom Script Extension, AD DS forest promotion

### 🔗 [Hardened NTFS File Server on Azure](https://github.com/DallaSamuel/CyberJKD-Labs/tree/main/phase-06/cloud-tech-techniques/cloud-system-admin-accelerator)

Deployed a 3-VM Windows environment with Terraform, then hardened it: per-user passwords in an RBAC-enabled **Key Vault**, NSG moved to the subnet, server public IPs removed behind a **NAT Gateway**. Checkov scans took the IaC from **19 passed / 17 failed to 31 passed / 0 failed** (7 documented exceptions). Built AGDLP NTFS permissions on 4 shares with Access-Based Enumeration, FSRM quotas, and audit logging that captured a denied access attempt.

**Skills:** Terraform, Key Vault, NAT Gateway, Checkov, NTFS/AGDLP, FSRM, GPO, PowerShell

---

## 🖥️ Windows & Identity

### 🔗 [Active Directory Environment on Azure](https://github.com/DallaSamuel/CyberJKD-Labs/tree/main/phase-03)

Built a domain on Windows Server 2025 with **5 OUs and 4 role-based security groups**, plus a Group Policy (12-character passwords, 15-minute screen lock, USB storage blocked). Ran the account lifecycle with the AD GUI and PowerShell: forced-change resets, unlocks, offboarding disables, and a 90-day inactive-account audit.

---

## 🔍 Monitoring, Vulnerability Management & Analysis

### 🔗 [Splunk Enterprise SIEM on Azure](https://github.com/DallaSamuel/CyberJKD-Labs/tree/main/phase-02)

Ingested live Linux auth logs, wrote 3 SPL detections, and built a High-severity **Brute Force SSH alert** and dashboard that surfaced probing from **3 real external IPs within hours**.

### 🔗 [Nessus Vulnerability Scanning on Azure](https://github.com/DallaSamuel/CyberJKD-Labs/tree/main/phase-02)

Compared unauthenticated and credentialed scans across two regions (**0 vs. 2 Critical CVEs**, CVSS 9.8 and 9.1) and wrote a 6-action remediation plan.

### 🔗 [ServiceNow Vulnerability Ticketing](https://github.com/DallaSamuel/CyberJKD-Labs/tree/main/phase-02)

Logged 6 findings as parent/child incidents with CVSS-to-priority mapping, registered the Azure VM as a CMDB CI, and resolved 2 with documented fixes.

### 🔗 [Wireshark & Network Analysis on Azure](https://github.com/DallaSamuel/CyberJKD-Labs/tree/main/phase-03)

Captured and analyzed traffic from an Azure Windows 11 VM, tracing DNS lookups and TCP/TLS handshakes with display filters and TCP stream reconstruction.

### 🔗 [Malware Analysis & Reverse Engineering](https://github.com/DallaSamuel/CyberJKD-Labs/tree/main/phase-04/cyb405-ethical_hacking_coursework_%28miva%29)

Analyzed a C2-simulation binary with strings, readelf, strace, tcpdump, and Ghidra, built a 5-row IOC table, and wrote a Suricata rule to detect the beaconing.

---

## 🧱 Foundations

### 🔗 [Linux Hardening Lab](https://github.com/DallaSamuel/linux-hardening-lab) + [Hardening Script](https://github.com/DallaSamuel/linux-hardening-script)

Audited and hardened Kali Linux (WSL2): disabled 4 unnecessary services (closing exposed RDP ports 3389 and 3350), enforced key-only SSH, and configured UFW. Automated the process in a Bash script that audits ports before and after and saves a timestamped report.

### 🔗 [Brute Force Simulation + Detection](https://github.com/DallaSamuel/CyberJKD-Labs/tree/main/phase-01)

Attacked an Ubuntu server with Hydra from Kali, detected the attacker with a Python log parser, blocked it with UFW, and verified the block.

### 🔗 [Network Segmentation with pfSense](https://github.com/DallaSamuel/CyberJKD-Labs/tree/main/phase-01)

Built a WAN/LAN/DMZ network and verified isolation with ping tests.

---

## ⚙️ Toolbox

- **Cloud & IaC:** Azure, Terraform, Key Vault, NSG, NAT Gateway, Checkov, Azure CLI
- **Windows & Identity:** Active Directory, Group Policy, NTFS/AGDLP, FSRM, PowerShell
- **Security & Monitoring:** Splunk, Nessus, Wireshark, Suricata, Ghidra, Hydra
- **ITSM & Scripting:** ServiceNow, Python 3, Bash, Git

## 📈 Next Labs

Microsoft Entra ID with Azure RBAC · Azure Monitor and storage

## 🎯 Career Direction

Seeking a **Junior Azure / Cloud Operations** role (or Windows systems admin / IT support) where I can apply infrastructure-as-code, identity, and monitoring skills in a real environment.

---

📧 dallasamuel233@gmail.com · 🔗 [LinkedIn](https://www.linkedin.com/in/dallasamuel) · 🗺️ [Roadmap](https://dallasamuel.github.io/CyberJKD-Roadmap) · 📅 [Book a call](https://calendly.com/dallasamuel/intro-call)
