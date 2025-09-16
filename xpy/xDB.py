#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    xPY, Gestion des bases de données
# Auteur:          Jacques Brunel, d'après Yvan LUCAS Noethys
# Copyright:       (c) 2019-04 
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os
import wx
import subprocess
import sqlite3
import copy
import xshelve

DICT_CONNEXIONS = {}

def GetConfigs():
    # appel des params de connexion stockés dans UserProfile et data
    cfg = xshelve.ParamUser()
    grpUSER = cfg.GetDict(groupe='USER', close=False)
    grpAPPLI = cfg.GetDict(groupe='APPLI')
    # appel des params de connexion stockés dans Data shared
    cfg = xshelve.FileShelve()
    grpCONFIGS = cfg.GetDict(groupe='CONFIGS')
    return grpAPPLI,grpUSER,grpCONFIGS

def GetOneConfig(self, nomConfig=None, mute=False):
    # appel d'une configuration nommée, retourne le dict des params (à revoir qd choix possibles!!)
    cfg = xshelve.FileShelve()
    grpCONFIGS = cfg.GetDict(groupe='CONFIGS')
    config = None
    if not nomConfig:
        for dicConfig in grpCONFIGS['lstConfigs']:
            if dicConfig['db_reseau']['typeDB'] == 'Access':
                config = dicConfig['db_reseau']
        return config

class DB():
    # accès à la base de donnees principale

    def __init__(self, IDconnexion = None, config=None, nomFichier=None, mute=False):
        # config peut être soit un nom de config soit un dictionaire
        #print(config,nomFichier,IDconnexion)
        self.echec = 1
        self.IDconnexion = IDconnexion
        self.nomBase = 'personne!'
        self.isNetwork = False
        self.lstTables = None
        self.lstIndex = None
        self.grpConfigs = None
        self.dictAppli = None
        self.cfgParams = None
        self.erreur = None
        if nomFichier:
            self.OuvertureFichierLocal(nomFichier)
            return
        if not IDconnexion:
            self.connexion = None

            # appel des params de connexion stockés dans UserProfile et Data
            grpAPPLI, grpUSER, grpCONFIGS = GetConfigs()
            self.dictAppli = grpAPPLI
            self.grpConfigs = grpCONFIGS
            self.cfgParams = GetOneConfig(self, None, mute=mute)
            if not self.cfgParams :
                self.erreur = "Aucun fichier de paramètres de connexion trouvé!"
                return

            # Ouverture des bases de données selon leur type
            if 'typeDB' in self.cfgParams:
                self.typeDB = self.cfgParams['typeDB'].lower()
            else : self.typeDB = 'Non renseigné'
            if 'typeDB' in self.cfgParams.keys() and  self.cfgParams['typeDB'].lower() in ['mysql','sqlserver']:
                self.isNetwork = True
                # Ouverture de la base de données
                self.ConnexionFichierReseau(self.cfgParams, mute=mute)
            elif 'typeDB' in self.cfgParams.keys() and  self.cfgParams['typeDB'].lower() in ['access','sqlite']:
                self.isNetwork = False
                self.ConnexionFichierLocal(self.cfgParams)
            else :
                mess = "xDB: Le type de Base de Données '%s' n'est pas géré!" % self.typeDB
                self.erreur = mess
                if not mute:
                    wx.MessageBox(mess)
                return

            if self.connexion:
                # Mémorisation de l'ouverture de la connexion et des requêtes
                if len(DICT_CONNEXIONS) == 0:
                    self.IDconnexion = 1
                else:
                    self.IDconnexion = sorted(DICT_CONNEXIONS.keys())[-1]+1
                DICT_CONNEXIONS[self.IDconnexion] = {}
                DICT_CONNEXIONS[self.IDconnexion]['isNetwork'] = self.isNetwork
                DICT_CONNEXIONS[self.IDconnexion]['typeDB'] = self.typeDB
                DICT_CONNEXIONS[self.IDconnexion]['connexion'] = self.connexion
                DICT_CONNEXIONS[self.IDconnexion]['cfgParams'] = self.cfgParams
        else:
            if self.IDconnexion in DICT_CONNEXIONS:
                # la connexion a été conservée (absence de DB.Close)
                self.isNetwork  = DICT_CONNEXIONS[self.IDconnexion]['isNetwork']
                self.typeDB     = DICT_CONNEXIONS[self.IDconnexion]['typeDB']
                self.connexion  = DICT_CONNEXIONS[self.IDconnexion]['connexion']
                self.cfgParams  = DICT_CONNEXIONS[self.IDconnexion]['cfgParams']
                if self.connexion: self.echec = 0

    def AfficheTestOuverture(self,info=""):
        style = wx.ICON_STOP
        if self.echec == 0: style = wx.ICON_INFORMATION
        accroche = ['Ouverture réussie ',"Echec d'ouverture "][self.echec]
        accroche += info
        retour = ['avec succès', ' SANS SUCCES !\n'][self.echec]
        mess = "%s\n\nL'accès à la base '%s' s'est réalisé %s" % (accroche,self.nomBase, retour)
        if self.erreur:
            mess += '\nErreur: %s'%self.erreur
        wx.MessageBox(mess, style=style)

    def OuvertureFichierLocal(self, nomFichier):
        """ Version LOCALE avec SQLITE """
        # Vérifie que le fichier sqlite existe bien
        if os.path.isfile(nomFichier) == False:
            wx.MessageBox("xDB: Le fichier local '%s' demande n'est pas present sur le disque dur."%nomFichier)
            self.echec = 1
            return
        # Initialisation de la connexion
        self.nomBase = nomFichier
        self.typeDB = "sqlite"
        self.ConnectSQLite()

    def ConnexionFichierLocal(self, config):
        self.connexion = None
        if config['serveur'][-1] != "\\":
            config['serveur'] += "\\"
        self.nomBase = config['serveur'] + config['nameDB']
        etape = 'Création du connecteur'
        try:
            if self.typeDB == 'sqlite':
                self.ConnectSQLite()
            elif self.typeDB.lower() == 'access':
                self.ConnectAccessOdbc()
            else:
                wx.MessageBox('xDB: Accès DB non développé pour %s' %self.typeDB)
        except Exception as err:
            wx.MessageBox("xDB: La connexion base de donnée a echoué à l'étape: %s, sur l'erreur :\n\n%s" %(etape,err))
            self.erreur = "%s\n\n: %s"%(err,etape)

    def ConnectAccessOdbc(self):
        # permet un acces aux bases access sans office
        if os.path.isfile(self.nomBase) == False:
            wx.MessageBox("xDB:Le fichier %s demandé n'est pas present sur le disque dur."% self.nomBase, style = wx.ICON_WARNING)
            return
        # Initialisation de la connexion
        try:
            import pyodbc
            """
            conn_str = (
                r'DRIVER={Microsoft Access Driver (*.mdb)};'
                'DBQ=D:\\Quadra\\Database\\cpta\\DC\\MATTH\\qcompta.mdb'
            )
            conn = pyodbc.connect(conn_str)
            """
            DRIVER = r'{Microsoft Access Driver (*.mdb)}'
            DBQ = self.nomBase
            PWD = '' # passWord
            self.connexion = pyodbc.connect('DRIVER={};DBQ={}'.format(DRIVER,DBQ,))
            self.cursor = self.connexion.cursor()
            allTables = self.cursor.tables()
            # Exemple code
            """
            self.cursor.execute("select * from Journaux;")
            for row in self.cursor.fetchall():
                print(row)
            self.cursor.close()
            del self.cursor
            self.connexion.close()"""
            self.echec = 0
        except Exception as err:
            wx.MessageBox("xDB.ConnectAcessOdbc:La connexion à la base access %s a echoué : \nErreur détectée :%s" %(self.nomBase,err),
                          style=wx.ICON_WARNING)
            self.erreur = err

    def ConnectSQLite(self):
        # Version LOCALE avec SQLITE
        #nécessite : pip install pysqlite
        # Vérifie que le fichier sqlite existe bien
        if os.path.isfile(self.nomBase) == False:
            wx.MessageBox("xDB: Le fichier %s demandé n'est pas present sur le disque dur."% self.nomBase, style = wx.ICON_WARNING)
            return
        # Initialisation de la connexion
        try:
            self.connexion = sqlite3.connect(self.nomBase.encode('utf-8'))
            self.cursor = self.connexion.cursor()
            self.echec = 0
        except Exception as err:
            wx.MessageBox("xDB: La connexion avec la base de donnees SQLITE a echoué : \nErreur détectée :%s" % err, style = wx.ICON_WARNING)
            self.erreur = err

    def ExecuterReq(self, req, mess=None, affichError=True):
        # Gestion de l'absence de connexion
        if self.echec >= 1:
            if not mess:
                origine = "xUTILS_DB.ExecuterReq"
            else: origine = mess
            if self.erreur != "ErreurPubliee" and affichError:
                mess = "Echec d'accès à la base de donnée\n\n%s"%origine
                wx.MessageBox(mess,"Ouverture DB",style = wx.ICON_ERROR)
            self.erreur = "ErreurPubliee"
            return mess
        if self.typeDB == 'access':
            self.recordset = []
            # methode Access ADO
            #self.cursor.Open(req, self.connexion)
            if not self.cursor.BOF:
                self.cursor.MoveFirst()
                while not self.cursor.EOF:
                    record = []
                    go = True
                    i=0
                    while go:
                        try:
                            record.append(self.cursor(i).value)
                            i += 1
                        except Exception:
                            go = False
                    self.recordset.append(record)
                    self.cursor.MoveNext()
                self.retourReq = "ok"
            else:
                self.retourReq = "Aucun enregistrement"
            #self.cursor.Close()
        # autres types de connecteurs que access
        else:
            # purge d'existant non lu
            if hasattr(self.cursor,'with_rows') and self.cursor.with_rows:
                try:
                    rows = self.cursor.fetchall()
                    if len(rows) > 0:
                        print(len(rows),"lignes non lues")
                except:
                    pass
            # Exécute la requête
            try:
                self.cursor.execute(req)
                self.retourReq = 'ok'
            except Exception as err:
                self.echec = 1
                if mess:
                    self.retourReq = mess +'\n%s\n'%err
                else: self.retourReq = 'Erreur xUTILS_DB\n\n'
                self.retourReq +=  ("%s\n\n\nErreur ExecuterReq:\n%s"% (req, str(err)))
                if affichError:
                    wx.MessageBox(self.retourReq,"Erreur accès BD",style=wx.ICON_ERROR)
            return self.retourReq

    def ResultatReq(self):
        if self.echec == 1 : return []
        resultat = []
        try :
            if self.typeDB == 'access':
                resultat = self.recordset
            else:
                resultat = self.cursor.fetchall()
                # Pour contrer MySQL qui fournit des tuples alors que SQLITE fournit des listes
                if self.typeDB == 'mysql' and type(resultat) == tuple :
                    resultat = list(resultat)
        except :
            pass
        return resultat

    def DonneesInsert(self,donnees):
        # décompacte les données en une liste  ou liste de liste pour requêtes Insert
        donneesValeurs = '('
        def Compose(liste):
            serie = ''
            for valeur in liste:
                if isinstance(valeur,(int,float)):
                    val = "%s, " %str(valeur)
                elif isinstance(valeur, (tuple, list,dict)):
                    val = "'%s', "%str(valeur)[1:-1].replace('\'', '')
                elif valeur == None or valeur == '':
                    val = "NULL, "
                else:
                    val = "'%s', "%str(valeur).replace('\'', '')
                serie += "%s"%(val)
            return serie[:-2]
        if isinstance(donnees[0], (tuple,list)):
            for (liste) in donnees:
                serie = Compose(liste)
                donneesValeurs += "%s ), ("%(serie)
            donneesValeurs = donneesValeurs[:-4]
        else:
            donneesValeurs += "%s"%Compose(donnees)
        return donneesValeurs +')'

    def ReqInsert(self,nomTable="",lstChamps=[],lstlstDonnees=[],lstDonnees=None,commit=True, mess=None,affichError=True):
        """ Permet d'insérer les lstChamps ['ch1','ch2',..] et lstlstDonnees [[val11,val12...],[val21],[val22]...]
            self.newID peut être appelé ensuite pour récupérer le dernier'D """
        if lstDonnees:
            if len(lstDonnees[0]) != 2: raise("lstDonnees doit être une liste de tuples (champ,donnee)")
            lsttemp=[]
            lstChamps=[]
            lstlstDonnees = []
            for (champ,donnee) in lstDonnees:
                lstChamps.append(champ)
                lsttemp.append(donnee)
            lstlstDonnees.append(lsttemp)
        if len(lstChamps)* len(lstlstDonnees) == 0:
            if affichError:
                mess = ('%s\n\nChamps ou données absents' % mess)
                raise Exception(mess)
            return mess

        valeurs = self.DonneesInsert(lstlstDonnees)
        champs = '( ' + str(lstChamps)[1:-1].replace('\'','') +' )'
        req = """INSERT INTO %s 
              %s 
              VALUES %s ;""" % (nomTable, champs, valeurs)
        self.retourReq = "ok"
        self.newID= 0
        try:
            # Enregistrement
            self.cursor.execute(req)
            if commit == True :
                self.Commit()
            # Récupération de l'ID
            if self.typeDB == 'mysql' :
                # Version MySQL
                self.cursor.execute("SELECT LAST_INSERT_ID();")
            else:
                # Version Sqlite
                self.cursor.execute("SELECT last_insert_rowid() FROM %s" % nomTable)
            self.newID = self.cursor.fetchall()[0][0]
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess +'\n%s\n'%err
            else: self.retourReq = 'Erreur xUTILS_DB\n\n'
            self.retourReq +=  ("ReqInsert:\n%s\n\nErreur detectee:\n%s"% (req, str(err)))
            if affichError:
                raise Exception(self.retourReq)
        return self.retourReq

    def CoupleMAJ(self,champ, valeur):
        nonetype = type(None)
        if isinstance(valeur,(int,float)):
            val = "%s, " %str(valeur)
        elif isinstance(valeur, (nonetype)):
            val = "NULL, "
        elif isinstance(valeur, (tuple, list,dict)):
            val = str(valeur)[1:-1]
            val = val.replace("'","")
            val = "'%s', "%val
        else: val = "\"%s\", "%str(valeur)
        couple = " %s = %s"%(champ,val)
        return couple

    def DonneesMAJ(self,donnees):
        # décompacte les données en une liste de couples pour requêtes MAJ
        donneesCouples = ""
        if isinstance(donnees, (tuple,list)):
            for (champ,valeur) in donnees:
                couple = self.CoupleMAJ(champ, valeur)
                donneesCouples += "%s"%(couple)
        elif isinstance(donnees,dict):
            for (champ, valeur) in donnees.items():
                couple = self.CoupleMAJ(champ, valeur)
                donneesCouples += "%s" % (couple)
        else: return None
        donneesCouples = donneesCouples[:-2]+' '
        return donneesCouples

    def ListesMAJ(self,lstChamps,lstDonnees):
        # assemble des données en une liste de couples pour requêtes MAJ
        donneesCouples = ''
        for ix in range(len(lstChamps)):
            couple = self.CoupleMAJ(lstChamps[ix], lstDonnees[ix])
            donneesCouples += "%s"%(couple)
        donneesCouples = donneesCouples[:-2]+' '
        return donneesCouples

    def ReqMAJ(self, nomTable='',
               lstDonnees=None,
               nomChampID=None,ID=None,condition=None,
               lstValues=[],lstChamps=[],
               mess=None, affichError=True, IDestChaine = False):
        """ Permet de mettre à jour des lstDonnees présentées en dic ou liste de tuples
            lstDonnees est  [('champ1', valeur1),('champ1', valeur1)...]
            lstValues est [(valeur1, valeur2...] associées à lstChamps
        """
        # si couple est None, on en crée à partir de lstChamps et lstValues
        if lstDonnees :
            update = self.DonneesMAJ(lstDonnees)
        elif (len(lstChamps) > 0) and (len(lstChamps) == len(lstValues)):
            update = self.ListesMAJ(lstChamps,lstValues)

        if nomChampID and ID:
            # un nom de champ avec un ID vient s'ajouter à la condition
            if IDestChaine == False and (isinstance(ID, int )):
                condID = " (%s=%d) "%(nomChampID, ID)
            else:
                condID = " (%s='%s') "%(nomChampID, ID)
            if condition:
                condition += " AND %s "%(condID)
            else: condition = condID
        elif (not condition) or (len(condition.strip())==0):
            # si pas de nom de champ et d'ID, la condition ne doit pas être vide sinon tout va updater
            condition = " FALSE "
        req = "UPDATE %s SET  %s WHERE %s ;" % (nomTable, update, condition)
        # Enregistrement
        try:
            self.cursor.execute(req,)
            self.Commit()
            if self.cursor.rowcount > 0:
                self.retourReq = "ok"
            else:
                self.retourReq = "ok inchangé! %s"%req
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess + '\n%s\n' % err
            else:
                self.retourReq = 'Erreur xUTILS_DB\n\n'
            self.retourReq += ("ReqMAJ:\n%s\n\nErreur detectee:\n%s" % (req, str(err)))
            if affichError:
                raise Exception(self.retourReq)
        return self.retourReq

    def ReqDEL(self, nomTable,champID="",ID=None, condition="", commit=True, mess=None, affichError=True):
        """ Suppression d'un enregistrement ou d'un ensemble avec condition de type where"""
        if len(condition)==0:
            if isinstance(ID,str):
               condition = champID+" = %s"%ID
            elif isinstance(ID,(int,float)):
               condition = champID+" = %d"%int(ID)
        self.retourReq = "ok"
        req = "DELETE FROM %s WHERE %s ;" % (nomTable, condition)
        try:
            self.cursor.execute(req)
            if commit == True :
                self.Commit()
                self.retourReq = "ok"
        except Exception as err:
            self.echec = 1
            if mess:
                self.retourReq = mess + '\n\n'
            else:
                self.retourReq = 'Erreur xUTILS_DB\n\n'
            self.retourReq += ("ReqMAJ:\n%s\n\nErreur detectee:\n%s" % (req, str(err)))
            if affichError:
                raise Exception(self.retourReq)
        return self.retourReq

    def Commit(self):
        if self.connexion:
            self.connexion.commit()

    def Close(self):
        try :
            self.connexion.close()
            del DICT_CONNEXIONS[self.IDconnexion]
        except :
            pass

    def IsTableExists(self, nomTable=""):
        """ Vérifie si une table donnée existe dans la base """
        tableExists = False
        if not self.lstTables :
            # ne charge qu'une fois la liste des tables
            self.lstTables = self.GetListeTables()
        if nomTable.lower() in self.lstTables :
            tableExists = True
        return tableExists

    def IsIndexExists(self, nomIndex=""):
        """ Vérifie si un index existe dans la base """
        indexExists = False
        if not self.lstIndex :
            # ne charge qu'une fois la liste des tables
            self.lstIndex = self.GetListeIndex()
        if nomIndex in self.lstIndex :
            indexExists = True
        return indexExists

    def CtrlTables(self, parent, dicTables, tables):
        # création de table ou ajout|modif des champs selon description fournie
        if not tables:
            tables = dicTables.keys()
        mess = None
        for nomTable in tables:
            if nomTable in ('utilisateurs','droits'):
                continue
            # les possibles vues sont préfixées v_ donc ignorées
            if nomTable[:2] == "v_":
                continue
            if not self.IsTableExists(nomTable):
                ret = self.CreationUneTable(dicTables=dicTables,nomTable=nomTable)
                mess = "Création de la table de données %s: %s" %(nomTable,ret)
            else:
                # controle des champs
                tableModel = dicTables[nomTable]
                lstChamps = self.GetListeChamps(nomTable)
                lstNomsChamps = [ x[0] for x in lstChamps]
                lstTypesChamps = [ x[1] for x in lstChamps]
                mess = "Champs: "
                for (nomChampModel, typeChampModel, info) in tableModel:
                    ret = None
                    # ajout du champ manquant
                    if not nomChampModel.lower() in lstNomsChamps:
                        ret = self.AjoutChamp(nomTable,nomChampModel,dicTables)
                    else:
                        # modif du type de champ
                        typeChamp = lstTypesChamps[lstNomsChamps.index(nomChampModel.lower())]
                        if not typeChampModel.lower()[:3] == typeChamp[:3]:
                            ret  = self.ModifTypeChamp(nomTable,nomChampModel,typeChampModel)
                        # modif de la longueur varchar
                        elif typeChamp[:3] == "var":
                            lgModel = typeChampModel.split("(")[1].split(")")[0]
                            lg = typeChamp.split("(")[1].split(")")[0]
                            if not lgModel == lg:
                                ret  = self.ModifTypeChamp(nomTable,nomChampModel,typeChampModel)
                    if ret:
                        mess += "; %s.%s: %s"%(nomTable,nomChampModel,ret)
            if mess and mess != "Champs: ":
                print(mess)
                # Affichage dans la StatusBar
                if parent and mess:
                    parent.mess += "%s %s, "%(nomTable,ret)
                    parent.SetStatusText(parent.mess[-200:])
        if parent:
            parent.mess += "- CtrlTables Terminé"
            parent.SetStatusText(parent.mess[-200:])
        else:
            print(mess)

    def GetListeTables(self,lower=True):
        # appel des tables et des vues
        if self.typeDB == 'sqlite' :
            # Version Sqlite
            req = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            self.ExecuterReq(req)
            recordset = self.ResultatReq()
        else:
            # Version MySQL
            req = "SHOW FULL TABLES;"
            self.ExecuterReq(req)
            recordset = self.ResultatReq()
        lstTables = []
        for record in recordset:
            if lower:
                lstTables.append(record[0].lower())
            else: lstTables.append(record[0])
        return lstTables

    def GetListeChamps(self, nomTable=""):
        """ retrourne la liste des tuples(nom,type) des champs de la table donnée """
        lstChamps = []
        # dict de tables de liste
        if not hasattr(self,"ddTablesChamps"):
            self.dlTablesChamps = {}
        # un seul appel par table
        if not nomTable in self.dlTablesChamps.keys():
            if self.typeDB == 'sqlite':
                # Version Sqlite
                req = "PRAGMA table_info('%s');" % nomTable
                self.ExecuterReq(req)
                listeTmpChamps = self.ResultatReq()
                for valeurs in listeTmpChamps:
                    lstChamps.append((valeurs[1], valeurs[2]))
            else:
                # Version MySQL
                req = "SHOW COLUMNS FROM %s;" % nomTable
                self.ExecuterReq(req)
                listeTmpChamps = self.ResultatReq()
                for valeurs in listeTmpChamps:
                    lstChamps.append((valeurs[0].lower(), valeurs[1].lower()))
            self.dlTablesChamps[nomTable] = lstChamps
        # la table a déjà été appellée
        else: lstChamps = self.dlTablesChamps[nomTable]
        return lstChamps

if __name__ == "__main__":
    app = wx.App()
    os.chdir("..")
    db = DB()
    db.AfficheTestOuverture()
