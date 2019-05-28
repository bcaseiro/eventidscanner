# TO DO List:
# 1) Pegar a lista de todos os logons e ver o que foi fora do horario comercial (seg-sexta e final de semana) e logar num arquivo .LOG.
# 2) O resultado de cada use-case exportar para um arquivo .LOG para que seja possivel depois checar contra o Password Safe para ver se houveram requests para estes horarios.
# DONE - 3) Para evitar multiplos eventos, filtrar somente os eventos se a hora e o minuto for diferente. nao importando se foi em diferentes segundos. 4624 Log type 3, muito evento!
#
# -- Fazer prgorama que veja a data do ultimo logon na estacao local: net user <usuario> e no dominio: net user <domainuser> /domain ... a cada 30 minutos. Coleta isso num arquivo e depois
# vai no Cofre e veja se tem uma request valida nesse horario.. senao tiver, manda um alerta.
# 3) Pegar na lista de eventos de account lockout e bater a hora e tempo e comparar na lista de evento 4625, para tirar qual host o "caller" estava tentando logar qdo aconteceu account lockout
# Pegar as conexoes do Netstat e bater com a API do Web of Trust (Anomali usa isso)
# DONE - Inicio e Fim de cada sessao

import win32com.client, sys, re
count = 0

def WMIDateStringToDate(dtmDate):
    strDateTime = ""
    if (dtmDate[4] == 0):
        strDateTime = dtmDate[5] + '/'
    else:
        strDateTime = dtmDate[4] + dtmDate[5] + '/'
    if (dtmDate[6] == 0):
        strDateTime = strDateTime + dtmDate[7] + '/'
    else:
        strDateTime = strDateTime + dtmDate[6] + dtmDate[7] + '/'
        strDateTime = strDateTime + dtmDate[0] + dtmDate[1] + dtmDate[2] + dtmDate[3] + " " + dtmDate[8] + dtmDate[9] + ":" + dtmDate[10] + dtmDate[11] +':' + dtmDate[12] + dtmDate[13]
    return strDateTime


strComputer = "proxy-granular"
#strComputer = "server05"
#strComputer = "wkst-win10"
objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
objSWbemServices = objWMIService.ConnectServer(strComputer,"root\cimv2")
Eventos_4624 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4624 AND CategoryString = 'Logon'")
Eventos_4648 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4648 AND CategoryString = 'Logon'")
Eventos_4720 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4720 AND CategoryString = 'User Account Management'")
Eventos_4732 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4732 AND CategoryString = 'Security Group Management'")
Eventos_4740 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4740 AND CategoryString = 'User Account Management'")
Eventos_4724 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4724 AND CategoryString = 'User Account Management'")
Eventos_1102 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 1102 AND CategoryString = 'Log clear'")
Eventos_7045 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'System' AND EventCode = 7045")
Eventos_4698 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4698 AND CategoryString = 'Other Object Access Events'")
Eventos_4625 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4625 AND CategoryString = 'Logon'")
Eventos_4672 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4672 AND CategoryString = 'Special Logon'")
Eventos_4728 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4728 AND CategoryString = 'Security Group Management'")
Eventos_4647 = objSWbemServices.ExecQuery("SELECT * FROM Win32_NTLogEvent WHERE Logfile = 'Security' AND EventCode = 4647 AND CategoryString = 'Logoff'")


regex_hifen = re.compile('Account Name:\s\s\-')
regex_host = re.compile('Account Name:\s\s[A-Za-z0-9-]+\$')
regex_ANONYMOUS = re.compile('Account Name:\s\s[ANONYMOUS LOGON]+')
regex_SYSTEM = re.compile('Account Name:\s\s[SYSTEM]')


lista_usecase1 = []                #### Use case 1 - Logon Local no Domain Controller: Event ID 4624 - Logon Type: 2 - INteractive/Console Logon
lista_usecase2 = []                 ### Use Case 2 - Acesso via RDP
lista_usecase3 = []                 ### Use Case 3 - A user or computer logged on to this computer from the network. (( Gera evento pra caramba ))
lista_usecase4 = []                 ### Use Case 4 - evento 4648 - usuario entrou credenciais ou processo (aplicacao) se autenticou usando credenciais. Pega logon local na estacao
lista_usecase5 = []                 ### Use Case 5 - New User was created
lista_usecase6 = []                 ### Use Case 6 - A member was added to a security-enabled local group.
lista_usecase7 = []                 ### Use Case 7 - Account lockout
lista_usecase8 = []                 ### Use Case 8 - Um usuario troucou a senha de outra conta
lista_usecase9 = []                 ### Use Case 9 - Event Viewer de seguranca foi limpo - 1102
lista_usecase10 = []                ### Use Case 10 - Service was created - 7045
lista_usecase11 = []                ### Use Case 11 - Scheduled Task has been created - 4698
lista_usecase12 = []                ### Use Case 12 - Failed to logon - user or password is wrong - 4625
lista_usecase13 = []                ### Use Case 13 - ID 4672 - Privileged Account Logon (Special Privilege)
lista_usecase14 = []                ### Use Case 14 - User added to a Domain Security Group

sessions_list = []
logon_list = []
logoff_list = []
fullsession_list = []


#regex_UserValido = re.compile('New Logon:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+')

regex_UserValido = re.compile('New Logon:\r\n\tSecurity ID:\t\tS-\d-\d-\d\d-\d+-\d+-\d+-\d+\r\n\tAccount Name:\t\t[a-zA-Z0-9-]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+')
regex_UserValid_usecase2 = re.compile('New Logon:\n\sSecurity ID:\t\tS-\d-\d-\d\d-\d+-\d+-\d+-\d+\n\sAccount Name:\t\t[A-Za-z0-9-]+\n\sAccount Domain:\t\t[A-Za-z0-9-]+')

regex_LogonType_2 = re.compile('Logon Type:\t\t\t2')                            # Logon Type = 2 - Logon Local no DC
regex_LogonType_3 = re.compile('Logon Type:\t\t\t3')                            # Logon Type = 3 - Network	A user or computer logged on to this computer from the network.
regex_LogonType_10 = re.compile('Logon Type:\t\t\t10')                          # Logon Type = 10 - Logon Via

regex_WorkstationName = re.compile('Workstation Name:\t[A-Za-z0-9-]+')
regex_SourceNetworkAddress = re.compile('Source Network Address:\t[0-9.a-zA-Z]+')
regex_AccountWhoseCredentials = re.compile('Account Whose Credentials Were Used:\r\n\tAccount Name:\t\t[a-zA-Z0-9-]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+')
regex_TargetServer = re.compile('Target Server:\n\tTarget Server Name:\t[A-Za-z0-9-]+\n\tAdditional Information:\t[A-Za-z0-9-]+')

regex_LogonID = re.compile('New Logon:\r\n\tSecurity ID:\t\tS-\d-\d-\d\d-\d+-\d+-\d+-\d+\r\n\tAccount Name:\t\t[a-zA-Z0-9-]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+\r\n\tLogon ID:\t\t[A-Za-z0-9-]+')
regex_logoffID = re.compile('Security ID:\t\tS-\d-\d-\d\d-\d+-\d+-\d+-\d+\r\n\tAccount Name:\t\t[a-zA-Z0-9-]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+\r\n\tLogon ID:\t\t[A-Za-z0-9-]+')

#')


### Use Case 4
regex_NetworkAddress = re.compile('Network Address:\\t[A-Za-z0-9-.]+')           # Source - IP address from where a connection to the target server is being issued - Use case 4
regex_TargetHost = re.compile('Security ID:\\t\\tS[0-9-A-Za-z]+\\r\\n\\tAccount Name:\\t\\t[A-Za-z0-9-$]+')       # Host where the privileged account is connecting. Target host for Use Case 4  - Subject Account Name: Proxy-Granular$
regex_ProcessName = re.compile('Process Name:\t\t[A-Za-z:\\\\\s0-9&]+.exe')
                                


### Use Case 5 -- New user account has been created
regex_Evento4720_SourceUser = re.compile('Subject:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+')
regex_Evento4720_NewUser = re.compile('New Account:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-]+\r\n\tAccount Domain:\t\t[a-zA-Z0-9-]+')


### Use Case 6 -- User Added to a LOCAL Security Group.
regex_Evento4732_SourceUser = re.compile('Subject:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+')
regex_Evento4732__Member = re.compile('Member:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-,=]+')
regex_Evento4732_GroupName = re.compile('Group:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tGroup Name:\t\t[a-zA-Z0-9-\s]+\r\n\tGroup Domain:\t\t[a-zA-Z0-9-]+')


### Use Case 7 - Account lockout
regex_Evento4740_LogonHost = re.compile('Subject:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-$]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+')
regex_Evento4740_AffectedAccount = re.compile('Account That Was Locked Out:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[A-Za-z0-9-]+')
regex_Evento4740_SourceHost = re.compile('Caller Computer Name:\t[A-Za-z0-9-]+')

### Use Case 8 - An user changed the password of another use account
regex_Evento4724_Author = re.compile('Subject:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-$]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+')
regex_Evento4724_TargetAccount = re.compile('Target Account:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-$]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+')



### Use Case 9 - The audit log was cleared.
regex_Evento1102_Author = re.compile('Subject:\r\n\tSecurity ID:\t[A-Za-z0-9-]+\r\n\tAccount Name:\t[a-zA-Z0-9-$]+\r\n\tDomain Name:\t[A-Za-z0-9-]+')



### Use Case 10 - New service was installed on this system - ID 4697
regex_Evento7045_ServiceName = re.compile('Service File Name:\s\sService Name:\s\s[A-Za-z0-9-.]+')
regex_Evento7045_Service_FilePath= re.compile('Service File Name:\s[A-Z0-9a-z\W"-\\.\s]+')
regex_Evento7045_Author= re.compile('Service File Name:\s[A-Z0-9a-z%"-\\.\s]+')


### Use Case 11 - Scheduled Task has been created
regex_Evento4698_Author = re.compile('Account Name:\t\t[a-zA-Z0-9-$]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-.]+')
regex_Evento4698_TaskName = re.compile('Task Name: \t\t\\\\[a-zA-Z0-9-$]+')
regex_Evento4698_TaskPath = re.compile('<Command>[A-Za-z0-9-:\\\\.\s]+')
regex_Evento4698_WhenWillExecute = re.compile('<StartBoundary>\d\d\d\d-\d\d-\d\d[A-Za-z-0-9]+\d\d:\d\d:\d\d')
                                                              

### Use Case 12 - Failed to logon - user or password is wrong - 4625
regex_Evento4625_AccountFailedToLogon = re.compile('Account For Which Logon Failed:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[A-Za-z0-9-.@]+')
regex_Evento4625_DomainOfAccountFailedToLogon = re.compile('Account For Which Logon Failed:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[A-Za-z0-9-.@]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-.@]+')
regex_Evento4625_LogonType = re.compile('Logon Type:\t\t\t[0-9]+')


### Us Case 13 - Event ID 4672 - Privileged Account Logon
regex_Evento4672_PrivAccount = re.compile('Subject:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+')



### Use Case 14 -- User Added to a DOMAIN Security Group.
regex_Evento4728_SourceUser = re.compile('Subject:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-]+\r\n\tAccount Domain:\t\t[A-Za-z0-9-]+')
regex_Evento4728__Member = re.compile('Member:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tAccount Name:\t\t[a-zA-Z0-9-,=]+')
regex_Evento4728_GroupName = re.compile('Group:\r\n\tSecurity ID:\t\t[A-Za-z0-9-]+\r\n\tGroup Name:\t\t[a-zA-Z0-9-\s]+\r\n\tGroup Domain:\t\t[a-zA-Z0-9-]+')




for evento4624 in Eventos_4624:
    #print ('------------------------ INICIO-----')

    strList = " "
    try :
        for objElem in eventos_4624.Data :
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'
      
    
    if evento4624.Message != None:


### Use case 1 - Logon Local no Domain Controller: Event ID 4624 - Logon Type: 2 - INteractive/Console Logon

        if regex_UserValido.findall(evento4624.Message):

            logon_date_time = WMIDateStringToDate(evento4624.TimeWritten)
            logon_hora_minuto = logon_date_time[0:16] 

            LogonID_evento4624 = str(regex_LogonID.findall(evento4624.Message))
          
            LogonID_evento4624 = LogonID_evento4624.replace("\\t","")
            LogonID_evento4624 = LogonID_evento4624.replace("']","")
            LogonID_evento4624 = LogonID_evento4624.replace("Account Name:","")
            LogonID_evento4624 = LogonID_evento4624.replace("Account Domain:","")
            LogonID_evento4624 = LogonID_evento4624.replace("Logon ID:","")
            LogonID_evento4624 = LogonID_evento4624.split("\\r\\n")

            #print (LogonID_evento4624)

            if len(LogonID_evento4624) > 1:

                AccountName_evento4624 = LogonID_evento4624[3].strip() + '\\' + LogonID_evento4624[2].strip()
                LOGONID_evento4624 = LogonID_evento4624[4].strip()
                #LinkedLogonID_evento4624 = LogonID_evento4624[5].strip()
                
                #print (AccountName_evento4624)
                #print (LOGONID_evento4624)
                #print (LinkedLogonID_evento4624)
                LogonProcessName = str(regex_ProcessName.findall(evento4624.Message))
                LogonProcessName = LogonProcessName.replace("['Process Name:\\t\\t","")
                LogonProcessName = LogonProcessName.replace("']","")
                LogonProcessName = str(LogonProcessName.lower())
                #print (LogonProcessName)


                SourceNetworkAddress = str(regex_SourceNetworkAddress.findall(evento4624.Message))
                #print (SourceNetworkAddress)
                SourceNetworkAddress = SourceNetworkAddress.replace("['","")
                SourceNetworkAddress = SourceNetworkAddress.replace("']","")
                SourceNetworkAddress = SourceNetworkAddress.split('\\t')
                
                if len(SourceNetworkAddress) <= 1:
                    SourceNetworkAddress = ''
                else:
                    SourceNetworkAddress = SourceNetworkAddress[1]

                
                    

                
                session_start = str(LOGONID_evento4624) + ' | ' + str(logon_date_time) + ' | ' + str(AccountName_evento4624) + ' | ' + SourceNetworkAddress + ' |  ' + str(strComputer)
                #print (session_start)

                if session_start not in logon_list:
                    logon_list.append(session_start)


    ################################################## LOGOFF ID #############################################
                
            for evento4647 in Eventos_4647:
                strList = " "
                try:
                    for objElem in eventos_4647:
                        strList = strList + objElem + ","
                except:
                    strList = strList + 'null'

                if evento4647.Message != None:

                    logoff_date_time = WMIDateStringToDate(evento4647.TimeWritten)
                    logoff_hora_minuto = logoff_date_time[0:16]
                   
                    logoff_evento4647 = str(regex_logoffID.findall(evento4647.Message))
                    
                    logoff_evento4647 = logoff_evento4647.replace("']","")
                    logoff_evento4647 = logoff_evento4647.replace("']","")
                    logoff_evento4647 = logoff_evento4647.replace("['","")
                    logoff_evento4647 = logoff_evento4647.replace("\\t","")
                    logoff_evento4647 = logoff_evento4647.replace("Account Name:","")
                    logoff_evento4647 = logoff_evento4647.replace("Account Domain:","")
                    logoff_evento4647 = logoff_evento4647.replace("Logon ID:","")
                    logoff_evento4647 = logoff_evento4647.split("\\r\\n")
                                                           
             
                    logoff_account = logoff_evento4647[2] + '\\' + logoff_evento4647[1]
                    logoff_ID = logoff_evento4647[3]
                    
                    #print (logoff_ID, logoff_account)

                    #print (LOGONID_evento4624)

                    #if LOGONID_evento4624 == logoff_evento4647:
                    #print ('Session Started: ', logon_hora_minuto)
                    #print ('Session Logoff: ', logoff_hora_minuto)
                    #print ('Account Name: ', AccountName_evento4624, logoff_account)
                    #print ('Logon e Logoff IDs ', LOGONID_evento4624, ' --- ', logoff_ID)

                    sessions_logoff = logoff_ID + " | " + logoff_date_time + ' | ' + logoff_account

                    if sessions_logoff not in logoff_list:
                        logoff_list.append(sessions_logoff)
                    

            
            if regex_LogonType_2.findall(evento4624.Message):            
                texto3 = str(regex_UserValido.findall(evento4624.Message))
                user_account = texto3.replace("New Logon:\\r\\n\\t","")
                user_account2 = user_account.replace("\\t","")
                user_account3 = user_account2.replace(user_account2[0:64],'')
                user_account4 = user_account3.replace("']","")
            
                temp = []
                temp = user_account4.split('\\r\\n')

                logon_domain = temp[1][15:]
                logon_account = temp[0][12:]
                logon_account = logon_account.replace(':','')
                
                

                ## Pegando o nome do Target Host
                workstation_name = str(regex_WorkstationName.findall(evento4624.Message))
                trata_workstationname = workstation_name.replace("['","")
                trata2_workstationname = trata_workstationname.replace("']","")
                trata3_workstationname = trata2_workstationname.split('\\t')
                workstation_name2 = trata3_workstationname[1]

                item_usecase1 = str(logon_hora_minuto) + ' | ' + 'Workstation Name: ' + str(workstation_name2) + ' | ' + str(logon_domain) + '\\' + str(logon_account)  + ' | Use Case 1: Event ID 4624 - Interactive - A user logged on to this computer.'

                if item_usecase1 not in lista_usecase1:
                    lista_usecase1.append(item_usecase1)
    


        
            ### Use case 2 - Logon via RDP: Event ID 4624 - Logon Type: 10 - INteractive/Console Logon
                    
            if regex_LogonType_10.findall(evento4624.Message):
 
                texto02 = str(regex_UserValido.findall(evento4624.Message))
                user_account = texto02.replace("New Logon:\\r\\n\\t","")
                user_account2 = user_account.replace("\\t","")
                user_account3 = user_account2.replace(user_account2[0:64],'')
                user_account4 = user_account3.replace("']","")
            
                temp = []
                temp = user_account4.split('\\r\\n')

                logon_domain = temp[1][15:]
                logon_account = temp[0][12:]
                logon_account = logon_account.replace(':','')
                logon_date_time = WMIDateStringToDate(evento4624.TimeWritten)
                

                ## Pegando o nome do Target Host
                workstation_name = str(regex_WorkstationName.findall(evento4624.Message))
                trata_workstationname = workstation_name.replace("['","")
                trata2_workstationname = trata_workstationname.replace("']","")
                trata3_workstationname = trata2_workstationname.split('\\t')
                workstation_name2 = trata3_workstationname[1]

                ## Source Network Address -- Source IP from where the RDP session was initiated:
                SourceNetworkAddress = str(regex_SourceNetworkAddress.findall(evento4624.Message))
                SourceNetworkAddress1 = SourceNetworkAddress.replace("['","")
                SourceNetworkAddress2 = SourceNetworkAddress1.replace("']","")
                SourceNetworkAddress3 = SourceNetworkAddress2.split('\\t')
                SourceNetworkAddress4 = SourceNetworkAddress3[1]
                

                item_usecase2 = str(logon_date_time) + ' | Source IP: ' + SourceNetworkAddress4 + ' | Target: ' + str(workstation_name2) + ' | ' + str(logon_domain) + '\\' + str(logon_account)  + ' | Use Case 2: Event ID 4624 - Logon Type 10 - Logon via RDP.'

                if item_usecase2 not in lista_usecase2:   
                    lista_usecase2.append(item_usecase2)


            ### Use case 3 - Event ID 4624 - Logon Type 3: Network	A user or computer logged on to this computer from the network.
                    
            if regex_LogonType_3.findall(evento4624.Message):
 
                texto02 = str(regex_UserValido.findall(evento4624.Message))
                user_account = texto02.replace("New Logon:\\r\\n\\t","")
                user_account2 = user_account.replace("\\t","")
                user_account3 = user_account2.replace(user_account2[0:64],'')
                user_account4 = user_account3.replace("']","")
            
                temp = []
                temp = user_account4.split('\\r\\n')

                logon_domain = temp[1][15:]
                logon_account = temp[0][12:]
                logon_account = logon_account.replace(':','')
                logon_date_time = WMIDateStringToDate(evento4624.TimeWritten)
                logon_hora_minuto = logon_date_time[0:16]                   ## Evitar muitos eventos para descartar acessos no mesmo minuto, mas diferente 

                ## Pegando o nome do Target Host
                workstation_name = str(regex_WorkstationName.findall(evento4624.Message))
                trata_workstationname = workstation_name.replace("['","")
                trata2_workstationname = trata_workstationname.replace("']","")
                trata3_workstationname = trata2_workstationname.split('\\t')
                workstation_name2 = trata3_workstationname[1]

                                
                SourceNetworkAddress = str(regex_SourceNetworkAddress.findall(evento4624.Message))
                SourceNetworkAddress1 = ''
                SourceNetworkAddress2 = ''
                SourceNetworkAddress3 = ''
                SourceNetworkAddress4 = ''

                if SourceNetworkAddress != '[]':
                    #print ('DIFERENTE')
                    SourceNetworkAddress1 = SourceNetworkAddress.replace("['","")
                    SourceNetworkAddress2 = SourceNetworkAddress1.replace("']","")
                    SourceNetworkAddress3 = SourceNetworkAddress2.split('\\t')
                    SourceNetworkAddress4 = SourceNetworkAddress3[1]
                

                    item_usecase3 = str(logon_hora_minuto) + ' Source IP: ' + SourceNetworkAddress4 + ' | Target: ' + str(workstation_name2) + ' | ' + str(logon_domain) + '\\' + str(logon_account)  + ' | Use Case 3: Event ID 4624 - Logon Type 3 -	A user or computer logged on to this computer from the network..'
                    
                    
                else:
                    #print ('Nao e diferente de vazio')
                    item_usecase3 = str(logon_hora_minuto) + ' Source IP: -' + ' | Target: ' + str(workstation_name2) + ' | ' + str(logon_domain) + '\\' + str(logon_account)  + ' | Use Case 3: Event ID 4624 - Logon Type 3 -	A user or computer logged on to this computer from the network..'
                    
                    
                    
                if item_usecase3 not in lista_usecase3:
                    
                    lista_usecase3.append(item_usecase3)
                    #print (objItem.Message)
    


###### Use Case 4 -- Evento 4648 - A logon was attempted using explicit credentials.
    #############
##  Catches: - Usuario logou em uma estacao de trabalho local, e o scan foi rodado nessa estacao de trabalho local... vai pegar o logon e vai bater com o last logon da conta no AD.
##  Catches: Aplicacoes que tem usuario amarrado em algum lugar, tipo pbauditor.exe, e outros.
## NAO PEGA - Se fez o logon na estacao de trabalho, porem, nao scaneou a estacao.. so' escaneou o domain controller. nao vai pegar.


for evento4648 in Eventos_4648:
    #print ('------------------------ INICIO-----')

    strList = " "
    try :
        for objElem in evento4648.Data :
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'
      
    
    if evento4648.Message != None:
        #print (evento4648.Message)
        


        if regex_AccountWhoseCredentials.findall(evento4648.Message):


            logon_date_time = WMIDateStringToDate(evento4648.TimeWritten)
            logon_hora_minuto = logon_date_time[0:16]                                   ## Evitar muitos eventos para descartar acessos no mesmo minuto, mas diferente
            
            texto4 = str(regex_AccountWhoseCredentials.findall(evento4648.Message))
            U4user_account = texto4.replace("['Account Whose Credentials Were Used:\\r\\n","")
            U4user_account1 = U4user_account.replace("\\tAccount Name:\\t\\t","")
            U4user_account2 = U4user_account1.replace("\\tAccount Domain:\\t\\t","")
            U4user_account3 = U4user_account2.replace("']","")
            U4user_account4 = []
            U4user_account4 = U4user_account3.split('\\r\\n')

            ## Aqui estao o dominio e a conta que foi usada.
            domain_account = U4user_account4[1]
            login_account = U4user_account4[0]

            if login_account[0:3] != 'DWM' and login_account[0:4] != 'UMFD':                 ### Excluindo eventos com o usuario DWM-
                #print (domain_account, login_account)

                detalhes_evento = str(evento4648.Message)
                SourceNetworkAddress = str(regex_NetworkAddress.findall(detalhes_evento))
                SourceNetworkAddress2 = SourceNetworkAddress.replace('Network Address:\\t','')           ### SourceAddress
                SourceNetworkAddress3 = SourceNetworkAddress2.replace("['","")
                SourceNetworkAddress4 = SourceNetworkAddress3.replace("']","")
                #print (SourceNetworkAddress4)

                ProcessName = ''
                ProcessName = str(regex_ProcessName.findall(detalhes_evento))
                ProcessName1 = ProcessName.replace("['Process Name:\\t\\t","")
                ProcessName2 = ProcessName1.replace("']","")

         
                if ProcessName2 not in 'C:\\\\Windows\\\\System32\\\\lsass.exe' and len(ProcessName2) > 2:                ## Excluding LSASS.EXE since it duplicates. qdo tem um logon vai ter um lsass.exe e o svchost
                    #print (ProcessName2) 
                    
                    
                    TargetHost = str(regex_TargetHost.findall(detalhes_evento))     
                    TargetHost1 = TargetHost.replace("']","")
                    TargetHost2 = TargetHost1.replace("['Security ID:\\t\\t","")
                    TargetHost3 = TargetHost2.split("\\t\\t")
                    TargetHost4 = TargetHost3[1]
                    #print (TargetHost4)                                                                     ### ==> Target Host (Subject Account Name) no eventviewer
                
                    #print (detalhes_evento)
                    #
                    item_usecase4 = str(logon_hora_minuto) + ' | Source Address: ' + str(SourceNetworkAddress4) + ' | Target Host: ' + str(TargetHost4) + ' | Account Name: ' + str(domain_account) + '\\' + str(login_account)  + ' | Process Name: ' + str(ProcessName2) + ' | Use Case 4: Evento 4648.' #  A logon was attempted using explicit credentials.'

                    if item_usecase4 not in lista_usecase4:
                        lista_usecase4.append(item_usecase4)




            ### Use case 5 - New user account has been created


for evento4720 in Eventos_4720:
    #print ('------------------------ INICIO-----')

    strList = " "
    try :
        for objElem in evento4720.Data :
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'
      
    
    if evento4720.Message != None:
        
        if regex_Evento4720_SourceUser.findall(evento4720.Message):

            logon_date_time = WMIDateStringToDate(evento4720.TimeWritten)
            
            texto05 = str(regex_Evento4720_SourceUser.findall(evento4720.Message))
            SourceUser4720 = texto05.replace("']",'')
            SourceUser4720_01 = SourceUser4720.replace('\\t','')
            SourceUser4720_02 = SourceUser4720_01.replace('Account Name:','')
            SourceUser4720_03 = SourceUser4720_02.replace('Account Domain:','')
            SourceUser4720_04 = SourceUser4720_03.split('\\r\\n')
            SourceUser4720_05 = SourceUser4720_04[3] + '\\' + SourceUser4720_04[2]
            #print (SourceUser4720_05)                                                   ### <== User who has created the other user. This is the source.


            NewUserCreated = str(regex_Evento4720_NewUser.findall(evento4720.Message))
            NewUserCreated_01 = NewUserCreated.replace("']",'')
            NewUserCreated_02 = NewUserCreated_01.replace('\\t','')
            NewUserCreated_03 = NewUserCreated_02.replace('Account Name:','')
            NewUserCreated_04 = NewUserCreated_03.replace('Account Domain:','')
            NewUserCreated_05 = NewUserCreated_04.split('\\r\\n')
            NewUserCreated_06 = NewUserCreated_05[3] + '\\' + NewUserCreated_05[2]
            #print (NewUserCreated_06)                                                   #### <== New User who was created by the Source User

            item_usecase5 = str(logon_date_time) + ' | Host: ' + str(strComputer) + ' | Source User: ' + str(SourceUser4720_05) + ' | New User Created: ' + str(NewUserCreated_06) + ' | Use Case 5: New User Account was created.'

            if item_usecase5 not in lista_usecase5:
                        lista_usecase5.append(item_usecase5)



####### Use case 6 - A member was added to a security group          #################

for evento4732 in Eventos_4732:
    # print ('------------------------ INICIO-----')

    strList = " "
    try:
        for objElem in evento4732.Data:
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'

    if evento4732.Message != None:

        if regex_Evento4732_SourceUser.findall(evento4732.Message):

            logon_date_time = WMIDateStringToDate(evento4732.TimeWritten)

            texto05 = str(regex_Evento4732_SourceUser.findall(evento4732.Message))
            SourceUser4732 = texto05.replace("']", '')
            SourceUser4732_01 = SourceUser4732.replace('\\t', '')
            SourceUser4732_02 = SourceUser4732_01.replace('Account Name:', '')
            SourceUser4732_03 = SourceUser4732_02.replace('Account Domain:', '')
            SourceUser4732_04 = SourceUser4732_03.split('\\r\\n')
            SourceUser4732_05 = SourceUser4732_04[3] + '\\' + SourceUser4732_04[2]
           # print (SourceUser4732_05)                                                   ### <== User (source) who has added an user to a Security Group.
            #print (evento4732.Message)  
                                                              
   
            UserAddedToGroup = str(regex_Evento4732__Member.findall(evento4732.Message))
            UserAddedToGroup1 = UserAddedToGroup.replace("']","")
            UserAddedToGroup2 = UserAddedToGroup1.replace("['Member:\\r\\n\\t","")
            UserAddedToGroup3 = UserAddedToGroup2.replace("Account Name:\\t\\t","")
            UserAddedToGroup4 = UserAddedToGroup3.split('\\r\\n\\t')
            UserAddedToGroup5 = UserAddedToGroup4[1]    
           # print (UserAddedToGroup5)                                                   ### <== Member.


            GroupName4732 = str(regex_Evento4732_GroupName.findall(evento4732.Message))
            GroupName4732_1 = GroupName4732.replace("']","")
            GroupName4732_2 = GroupName4732_1.replace("['Group:\\r\\n\\tSecurity ID:\\t\\t","")
            GroupName4732_3 = GroupName4732_2.replace("Group Name:\\t\\t","")
            GroupName4732_4 = GroupName4732_3.replace("Group Domain:\\t\\t","")
            GroupName4732_5 = GroupName4732_4.split("\\r\\n\\t")
            GroupName4732_6 = GroupName4732_5[2] + '\\' + GroupName4732_5[1]
            #print (evento4732.Message) 
            #print (GroupName4732_6)                                                         ### <== Group Name where the user was added.
            #sys.exit()

            item_usecase6 = str(logon_date_time) + ' | Host: ' + str(strComputer) + ' | Who made the change: ' + str(SourceUser4732_05) + ' | Member: ' + str(UserAddedToGroup5) + ' | LOCAL Group Name: ' + str(GroupName4732_6) + ' | Use Case 6 - A member was added to a security-enabled local group.'

            if item_usecase6 not in lista_usecase6:
                        lista_usecase6.append(item_usecase6)



########## eVENTO 4740 - Use case 7:  Account Lockout            #############


for evento4740 in Eventos_4740:
    # print ('------------------------ INICIO-----')

    strList = " "
    try:
        for objElem in evento4740.Data:
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'
    

    if evento4740.Message != None:

        logon_date_time = WMIDateStringToDate(evento4740.TimeWritten)

        AffectedAccount = str(regex_Evento4740_AffectedAccount.findall(evento4740.Message))
        AffectedAccount1 = AffectedAccount.replace("']","")
        AffectedAccount2 = AffectedAccount1.replace("['Account That Was Locked Out:\\r\\n\\tSecurity ID:\\t\\t","")
        AffectedAccount3 = AffectedAccount2.replace("Account Name:","")
        AffectedAccount4 = AffectedAccount3.replace("\\t","")
        AffectedAccount5 = AffectedAccount4.split("\\r\\n")
        AffectedAccount6 = AffectedAccount5[1]                  ##### <<<=== Affected Conta
            
     
        LogonHost = str(regex_Evento4740_LogonHost.findall(evento4740.Message))  #['Subject:\r\n\tSecurity ID:\t\tS-1-5-18\r\n\tAccount Name:\t\tSERVER05$\r\n\tAccount Domain:\t\tBTLAB']
        LogonHost1 = LogonHost.replace("']","")
        LogonHost2 = LogonHost1.replace("['Subject:\\r\\n\\tSecurity ID:\\t\\t","")
        LogonHost3 = LogonHost2.replace("\\tAccount Name:\\t\\t","")
        LogonHost4 = LogonHost3.replace("\\tAccount Domain:\\t\\t","")
        LogonHost5 = LogonHost4.split("\\r\\n")
        LogonHost6 = LogonHost5[2] + '\\' + LogonHost5[1]       ## <<< === Domain Controler que detectou o account lockout.
                                                                                ### LogonHost - Na verdade nao eh o logonhost e sim o domain controller que o usuario tentou se autenticar.
                                                                                ### Nesse evento nao aparece o servidor que o usuario tentou acessar.
                                                                                ### No verdadeiro logonhost, vai aparecer 3 eventos 4625 dizendo q o  usuario errou a senha.
        
        
        
        SourceHost = str(regex_Evento4740_SourceHost.findall(evento4740.Message))
        SourceHost1 = SourceHost.replace("']","")
        SourceHost2 = SourceHost1.replace("['Caller Computer Name:\\t","")
        #print (SourceHost2)                                                         ### <<< === Host da onde partiu o account lockout
        

        item_usecase7 = str(logon_date_time) + ' | Host: ' + str(strComputer) + ' | Affected Account: ' + str(AffectedAccount6) + ' | SourceHost: ' + str(SourceHost2) + ' | Domain Controller: ' + str(LogonHost6) + ' | Use Case 7 - A user account was locked out.'

        if item_usecase7 not in lista_usecase7:
            lista_usecase7.append(item_usecase7)



########## Evenoto 4724 - Use case 8:  An user changed hte password of another user            #############


for evento4724 in Eventos_4724:
    # print ('------------------------ INICIO-----')

    strList = " "
    try:
        for objElem in evento4724.Data:
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'
    

    if evento4724.Message != None:
        #print (evento4724.Message)

        evento4724_date_time = WMIDateStringToDate(evento4724.TimeWritten)

        Author4724_01 = str(regex_Evento4724_Author.findall(evento4724.Message))
        Author4724_02 = Author4724_01.replace("']","")
        Author4724_03 = Author4724_02.replace("['Subject:\\r\\n\\tSecurity ID:\\t\\t","")
        Author4724_04 = Author4724_03.replace("\\tAccount Name:\\t\\t","")
        Author4724_05 = Author4724_04.replace("\\tAccount Domain:\\t\\t","")
        Author4724_06 = Author4724_05.split("\\r\\n")
        Author4724_07 = Author4724_06[2] + '\\' + Author4724_06[1]                          ## <<== Author - The use who has reseted someone's password.
        print (Author4724_07)
        

        TargetAccount4724_01 = str(regex_Evento4724_TargetAccount.findall(evento4724.Message))
        TargetAccount4724_02 = TargetAccount4724_01.replace("']","")
        TargetAccount4724_03 = TargetAccount4724_02.replace("['Target Account:\\r\\n\\tSecurity ID:\\t\\t","")
        TargetAccount4724_04 = TargetAccount4724_03.replace("\\tAccount Name:\\t\\t","")
        TargetAccount4724_05 = TargetAccount4724_04.replace("\\tAccount Domain:\\t\\t","")
        TargetAccount4724_06 = TargetAccount4724_05.split("\\r\\n")
        TargetAccount4724_07 = TargetAccount4724_06[2] + '\\' + TargetAccount4724_06[1]                          ## <<== Target Account - User who had his password reseted.
        print (TargetAccount4724_07)

        item_usecase8 = str(evento4724_date_time) + ' | Host: ' + str(strComputer) + ' | Author: ' + str(Author4724_07) + ' | Target Account: ' + str(TargetAccount4724_07) + " | Use Case 8 - An attempt was made to reset an account's password."

        if item_usecase8 not in lista_usecase8:
            lista_usecase8.append(item_usecase8)




########## Evenoto 1102 - Use case 9:  Security Event Viewer was cleared           #############


for evento1102 in Eventos_1102:
    # print ('------------------------ INICIO-----')

    strList = " "
    try:
        for objElem in evento1102.Data:
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'
    

    if evento1102.Message != None:
        #print (evento4724.Message)

        evento1102_date_time = WMIDateStringToDate(evento1102.TimeWritten)

        Author1102_01 = str(regex_Evento1102_Author.findall(evento1102.Message))
      
        Author1102_02 = Author1102_01.replace("']","")
 
        Author1102_03 = Author1102_02.replace("['Subject:\\r\\n\\tSecurity ID:\\t","")
                                            
        Author1102_04 = Author1102_03.replace("\\tAccount Name:\\t","")
       
        Author1102_05 = Author1102_04.replace("\\tDomain Name:\\t","")
        Author1102_06 = Author1102_05.split("\\r\\n")
        Author1102_07 = Author1102_06[2] + '\\' + Author1102_06[1]                          ## <<== Author - The user who cleared the security event log.
        #print (Author1102_07)
      

        item_usecase9 = str(evento1102_date_time) + ' | Host: ' + str(strComputer) + ' | Author: ' + str(Author1102_07) + " | Use Case 9 - Audit Log was cleared."

        if item_usecase9 not in lista_usecase9:
            lista_usecase9.append(item_usecase9)


########## Evenoto 7045 - Use case 10:  New service was installed on this system - psexec criando servicos nas maquinas remotas        #############


for evento7045 in Eventos_7045:
    # print ('------------------------ INICIO-----')

    strList = " "
    
    try:
        for objElem in evento7045.Data:
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'

    
    
    if evento7045.TimeGenerated != None:
        evento7045_date_time =  WMIDateStringToDate(evento7045.TimeGenerated)
        
        evento7045_temp = str(evento7045.Message)
        evento7045_temp1 = evento7045_temp.replace("A service was installed in the system.\r\n\r\nService Name:","")
        evento7045_temp2 = evento7045_temp1.replace("Service File Name:","")
        evento7045_temp3 = evento7045_temp2.split('\r\n')

        evento7045_ServiceName = evento7045_temp3[0].strip()
        evento7045_FilePath = evento7045_temp3[1].strip()
        
    if evento7045.User != None:
        evento7045_Author = evento7045.user
        #print ("User: ", evento7045.User)

    item_usecase10 = str(evento7045_date_time) + ' | Host: ' + str(strComputer) + ' | Author: ' + str(evento7045_Author) + " | Service Name: " + str(evento7045_ServiceName) + " | File Path: " + str(evento7045_FilePath) + " | Use Case 10 - New service was installed."

    if item_usecase10 not in lista_usecase10:
        lista_usecase10.append(item_usecase10)
       


########## Evenoto 4698 - Use case 11: New Scheduled Task has been created - TEM QUE HABILITAR nA GPO para auditar: AUDIT OTHER OBJECT ACCESS EVENTS     #############


for evento4698 in Eventos_4698:
    # print ('------------------------ INICIO-----')

    strList = " "
    
    try:
        for objElem in evento4698.Data:
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'

    
    if evento4698.TimeGenerated != None:
        evento4698_date_time =  WMIDateStringToDate(evento4698.TimeGenerated)
        #print (evento4698.Message)

        author_evento4698 = str(regex_Evento4698_Author.findall(evento4698.Message))
        author_evento4698_temp1 = author_evento4698.replace("['Account Name:\\t\\t","")
        author_evento4698_temp2 = author_evento4698_temp1.replace("Account Domain:\\t\\t","")
        author_evento4698_temp3 = author_evento4698_temp2.replace("']","")
        author_evento4698_temp4 = author_evento4698_temp3.split("\\r\\n\\t")
        author_evento4698 = author_evento4698_temp4[1] + '\\' + author_evento4698_temp4[0]
        #print (author_evento4698)                                                                   ### << === Who created the Scheduled Task

#'Account Name:\t\tAdministrator\r\n\tAccount Domain:\t\tBTLAB']

        TaskPath_evento4698_temp1 = str(regex_Evento4698_TaskPath.findall(evento4698.Message))
        TaskPath_evento4698_temp2 = TaskPath_evento4698_temp1.replace("['<Command>","")
        TaskPath_evento4698 = TaskPath_evento4698_temp2.replace("']","")
        #print (TaskPath_evento4698)                                                                 ### <<=== Task File Path is here

        evento4698_TaskName = str(regex_Evento4698_TaskName.findall(evento4698.Message))
        evento4698_TaskName1 = evento4698_TaskName.replace("']","")
        evento4698_TaskName2 = evento4698_TaskName1.split('\\\\')
        evento4698_TaskName3 = evento4698_TaskName2[1]
        #print (evento4698_TaskName3)                                                                ### <<=== Name of the scheduled task that was created
        
        
        WhenWillExecute_evento4698 = str(regex_Evento4698_WhenWillExecute.findall(evento4698.Message))
        WhenWillExecute_evento4698_temp1 = WhenWillExecute_evento4698.replace("']","")
        WhenWillExecute_evento4698_temp2 = WhenWillExecute_evento4698_temp1.split("<StartBoundary>")

        if len(WhenWillExecute_evento4698) <= 2:
            WhenWillExecute_evento4698 = ''
        else:
            WhenWillExecute_evento4698 = WhenWillExecute_evento4698_temp2[1]
        #print (WhenWillExecute_evento4698)                                                        ### << == Date when this scheduled task will be ran

        
            
        
        
        item_usecase11 = str(evento4698_date_time) + ' | Host: ' + str(strComputer) + ' | Author: ' + str(author_evento4698) + " | Task Name: " + str(evento4698_TaskName3) + " | File Path: " + str(TaskPath_evento4698) + " | Scheduled for: " + str(WhenWillExecute_evento4698) +  " | Use Case 11 - New scheduled task was created."

        if item_usecase11 not in lista_usecase11:
            lista_usecase11.append(item_usecase11)



######## Use Case 12 - Evento ID 4625 - Failed to log on - Bad username or password           #############

for evento4625 in Eventos_4625:
    
    strList = " "
    try :
        for objElem in evento4625.Data :
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'
      
    #print (evento4625.Message)
    if evento4625.Message != None:

        ## Estou tratando dominio separadamente, pois se o usuario deixar o dominio em branco e colocar no username bruno@btlab.ca, o campo Dominio vai estar em branco e vai quebrar o
        # regex que fiz para o nome da conta.

        evento4625_date_time =  WMIDateStringToDate(evento4625.TimeGenerated)
        
        DomainOfAccountWhichFailedLogon = str(regex_Evento4625_DomainOfAccountFailedToLogon.findall(evento4625.Message))
        DomainOfAccountWhichFailedLogon = DomainOfAccountWhichFailedLogon.replace("']","")
        DomainOfAccountWhichFailedLogon = DomainOfAccountWhichFailedLogon.split("Account Domain:\\t\\t")
        DomainOfAccountWhichFailedLogon = DomainOfAccountWhichFailedLogon[1]                              ### <<== Account's Domain


        AccoutWhichFailedLogon_evento4625 = str(regex_Evento4625_AccountFailedToLogon.findall(evento4625.Message))
        AccoutWhichFailedLogon_evento4625_temp1 = AccoutWhichFailedLogon_evento4625.replace("']","")
        AccoutWhichFailedLogon_evento4625_temp2 = AccoutWhichFailedLogon_evento4625_temp1.replace("\\t\\t","")
        AccoutWhichFailedLogon_evento4625_temp3 = AccoutWhichFailedLogon_evento4625_temp2.split("Account Name:")
        AccoutWhichFailedLogon_evento4625 = AccoutWhichFailedLogon_evento4625_temp3[1]                              ## <<== Account's Name


        SourceSystem_evento4625 = str(regex_WorkstationName.findall(evento4625.Message))
        SourceSystem_evento4625 = SourceSystem_evento4625.replace("']","")
        SourceSystem_evento4625 = SourceSystem_evento4625.split("['Workstation Name:\\t")
        SourceSystem_evento4625 = SourceSystem_evento4625[1]
        #print (SourceSystem_evento4625)                                                     ### <<=== System where that account's name tried to login - Campo Workstation Name


        LogonType_evento4625 = str(regex_Evento4625_LogonType.findall(evento4625.Message))
        LogonType_evento4625 = LogonType_evento4625.replace("']","")
        LogonType_evento4625 = LogonType_evento4625.split('\\t\\t\\t')
        LogonType_evento4625 = LogonType_evento4625[1]
        #print (LogonType_evento4625)
                                   



        FullAccountName = DomainOfAccountWhichFailedLogon + '\\' + AccoutWhichFailedLogon_evento4625
        
        item_usecase12 = str(evento4625_date_time) + ' | Host: ' + str(strComputer) + ' | Author: ' + str(FullAccountName) + " | Source System: " + str(SourceSystem_evento4625) + " | Logon Type: " + str(LogonType_evento4625) + " | Use Case 12 - Unknown user name or bad password."

        if item_usecase12 not in lista_usecase12:
            lista_usecase12.append(item_usecase12)

              


######## Use Case 13 - Evento ID 4672 - Privileged Account Logon           #############

for evento4672 in Eventos_4672:
    
    strList = " "
    try :
        for objElem in evento4672.Data :
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'

    #print (evento4672.Message)
      
    #print (evento4672.Message)
    if evento4672.Message != None:

        ## Estou tratando dominio separadamente, pois se o usuario deixar o dominio em branco e colocar no username bruno@btlab.ca, o campo Dominio vai estar em branco e vai quebrar o
        # regex que fiz para o nome da conta.

        evento4672_date_time =  WMIDateStringToDate(evento4672.TimeGenerated)
        logon_hora_minuto = evento4672_date_time[0:16] 
        
        PrivAccount_evento4672 = str(regex_Evento4672_PrivAccount.findall(evento4672.Message))
        PrivAccount_evento4672 = PrivAccount_evento4672.replace("']","")
        PrivAccount_evento4672 = PrivAccount_evento4672.replace('\\t','')
        PrivAccount_evento4672 = PrivAccount_evento4672.replace('Account Name:','')
        PrivAccount_evento4672 = PrivAccount_evento4672.replace('Account Domain:','')
        PrivAccount_evento4672 = PrivAccount_evento4672.split('\\r\\n')


        if len(PrivAccount_evento4672) > 2:
            
            if PrivAccount_evento4672[2][0:3] != 'DWM' and PrivAccount_evento4672[2][0:4] != 'UMFD':                 ### Excluindo eventos com o usuario DWM-

                PrivAccount_evento4672 = PrivAccount_evento4672[3] + '\\' + PrivAccount_evento4672[2]

                if PrivAccount_evento4672  != "NT\\SYSTEM":                         ## Excluding events with SYSTEM account
                    #print (PrivAccount_evento4672)

                    item_usecase13 = str(logon_hora_minuto) + ' | Host: ' + str(strComputer) + ' | Priv Account: ' + str(PrivAccount_evento4672) + " | Use Case 13 - Special privileges assigned to new logon."

                    if item_usecase13 not in lista_usecase13:
                        lista_usecase13.append(item_usecase13)




####### Use case 14 - A member was added to a DOMAIN security group          #################

for evento4728 in Eventos_4728:
    # print ('------------------------ INICIO-----')

    strList = " "
    try:
        for objElem in evento4728.Data:
            strList = strList + objElem + ","
    except:
        strList = strList + 'null'

    

    if evento4728.Message != None:

        if regex_Evento4728_SourceUser.findall(evento4728.Message):

            logon_date_time = WMIDateStringToDate(evento4728.TimeWritten)

            texto05 = str(regex_Evento4728_SourceUser.findall(evento4728.Message))
            SourceUser4728 = texto05.replace("']", '')
            SourceUser4728_01 = SourceUser4728.replace('\\t', '')
            SourceUser4728_02 = SourceUser4728_01.replace('Account Name:', '')
            SourceUser4728_03 = SourceUser4728_02.replace('Account Domain:', '')
            SourceUser4728_04 = SourceUser4728_03.split('\\r\\n')
            SourceUser4728_05 = SourceUser4728_04[3] + '\\' + SourceUser4728_04[2]
            #print (SourceUser4728_05)                                                   ### <== User (source) who has added an user to a Security Group.
            #print (evento4732.Message)
            
                                                              
   
            UserAddedToGroup = str(regex_Evento4728__Member.findall(evento4728.Message))
            UserAddedToGroup1 = UserAddedToGroup.replace("']","")
            UserAddedToGroup2 = UserAddedToGroup1.replace("['Member:\\r\\n\\t","")
            UserAddedToGroup3 = UserAddedToGroup2.replace("Account Name:\\t\\t","")
            UserAddedToGroup4 = UserAddedToGroup3.split('\\r\\n\\t')
            UserAddedToGroup5 = UserAddedToGroup4[1]
          
           # print (UserAddedToGroup5)                                                   ### <== Member.

            GroupName4728 = str(regex_Evento4728_GroupName.findall(evento4728.Message))
            GroupName4728_1 = GroupName4728.replace("']","")
            GroupName4728_2 = GroupName4728_1.replace("['Group:\\r\\n\\tSecurity ID:\\t\\t","")
            GroupName4728_3 = GroupName4728_2.replace("Group Name:\\t\\t","")
            GroupName4728_4 = GroupName4728_3.replace("Group Domain:\\t\\t","")
            GroupName4728_5 = GroupName4728_4.split("\\r\\n\\t")
            GroupName4728_6 = GroupName4728_5[2] + '\\' + GroupName4728_5[1]

            #print (GroupName4728)
            #print (GroupName4728_6)                                                         ### <== Group Name where the user was added.
            #print ('')
            #print (evento4728.Message)
            #sys.exit()
            

            item_usecase14 = str(logon_date_time) + ' | Host: ' + str(strComputer) + ' | Who made the change: ' + str(SourceUser4728_05) + ' | Member: ' + str(UserAddedToGroup5) + ' | DOMAIN Group: ' + str(GroupName4728_6) + ' | Use Case 14 - A member was added to a DOMAIN security-enabled local group.'

            if item_usecase14 not in lista_usecase14:
                        lista_usecase14.append(item_usecase14)







print ("Use Case 1: ")
print ("")
for a in lista_usecase1:
    print (a)
print ("")


print ("Use Case 2: ")
print ("")

for b in lista_usecase2:
    print (b)

print ("")
print ("Use Case 3: ")
print ("")

for c in lista_usecase3:
    print (c)
print (len(lista_usecase3))

print ("")
print ("Use Case 4:")
print ("")
for d in lista_usecase4:
    print (d)
print ("")


print ("")
print ("Use Case 5:")
print ("")
for e in lista_usecase5:
    print (e)
print ("")


print ("")
print ("Use Case 6:")
print ("")
for f in lista_usecase6:
    print (f)
print ("")


print ("")
print ("Use Case 7:")
print ("")
for g in lista_usecase7:
    print (g)
print ("")


print ("")
print ("Use Case 8:")
print ("")
for h in lista_usecase8:
    print (h)
print ("")


print ("")
print ("Use Case 9:")
print ("")
for i in lista_usecase9:
    print (i)
print ("")


print ("")
print ("Use Case 10:")
print ("")
for j in lista_usecase10:
    print (j)
print ("")



print ("")
print ("Use Case 11:")
print ("")
for k in lista_usecase11:
    print (k)
print ("")




print ("")
print ("Use Case 12:")
print ("")
for l in lista_usecase12:
    print (l)
print ("")


print ("")
print ("Use Case 13:")
print ("")
for m in lista_usecase13:
    print (m)
print ("")


print ("")
print ("Use Case 14:")
print ("")
for n in lista_usecase14:
    print (n)
print ("")




print ('SESSIONS:')
for logon in logon_list:
    logon = logon.split(' | ')
    logonid = logon[0]
    logondate = logon[1]
    logonaccount = logon[2]
    sourcehost = logon[3]
    analyzedhost = logon[4]

    for logoff in logoff_list:
        logoff = logoff.split(' | ')
        logoffid = logoff[0]
        logoffdate = logoff[1]
        logoffaccount = logoff[2]
        

        if logonid == logoffid:

            full_session = 'Start Date: ' + logondate + ' | Logoff Date: ' + logoffdate + ' | ' + logonaccount + ' | Source: ' + sourcehost + ' | Analyzed Host: ' + analyzedhost 
            fullsession_list.append(full_session)


for each_session in fullsession_list:
    print (each_session)
