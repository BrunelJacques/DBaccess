# !/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Application :    Projet XPY, gestion des paramètres de configuration
#                  soit dans un fichier user soit dans un repertoire partagé
# Licence:         Licence GNU GPL
#----------------------------------------------------------------------------

import wx
import os, sys
import shelve
import appdirs
import tempfile
import datetime

def DumpFile(dic):
        def DumpDic(dic,nbtab):
            nbtab+=2
            for cle, valeur in dic.items():
                if isinstance(valeur, (dict,list)):
                    print(nbtab * '\t',cle,'( %s %d val): '%(type(valeur), len(valeur)))
                else: print(nbtab * '\t', cle, ' : ' , valeur)
                if isinstance(valeur,dict): DumpDic(valeur,nbtab)
                if isinstance(valeur, list): DumpList(valeur, nbtab)
        def DumpList(lst,nbtab):
            nbtab+=2
            for valeur in lst:
                if isinstance(valeur, (dict,list)):
                    print(nbtab * '\t', '( %s %d valeurs ): ' % (type(valeur), len(valeur)))
                else: print(nbtab * '\t',  valeur)
                if isinstance(valeur,dict): DumpDic(valeur,nbtab)
                if isinstance(valeur, list): DumpList(valeur, nbtab)
        if len(dic) > 0:
            DumpDic(dic,-1)

def GetRepShared(ajout="data"):
    """ Retourne le chemin du répertoire principal """
    frozen = getattr(sys, 'frozen', '')
    # if not frozen on récupère le path de ce fichier
    if not frozen:
        rep = os.path.abspath(__file__)
        # la racine va s'arrête au niveau 'xpy' (if not frozen)
        repShared = rep.split(r'\xpy')[0]
    else:
        repShared = os.path.dirname(sys.executable)
    repShared = os.path.join(repShared, ajout)
    os.makedirs(repShared, exist_ok=True)
    return repShared

def GetRepTemp(ajout=""):
    chemin = tempfile.gettempdir()
    os.makedirs(chemin, exist_ok=True)
    return os.path.join(chemin, ajout)

def GetRepUser(ajout="xpy"):
    if not ajout: ajout = ""
    chemin = appdirs.user_config_dir(roaming=False)
    chemin = os.path.join(chemin, ajout)
    os.makedirs(chemin, exist_ok=True)
    return chemin

class FileShelve:
    # Gestion des paramètres dans un fichier accessible à tous via Shelve

    def __init__(self, nomFichier='Config', path='',flag='c', close=True):
        # recherche des configs dans la frame de lancement avec clé 'versus', puis dans UserProfile ou Data
        # le fichier est vu comme un quasi-dictionnaire, il contient le dictionnaire du groupe de paramètres
        # le versus 'data' ou 'user' sera la clé de stockage en mémoire dictMem
        self.flag = flag
        self.close = close
        self.dictMem= {}

        if not path:
            path = GetRepShared()
        self.closed = True
        self.dictFic = {}
        os.makedirs(path, exist_ok=True)
        self.chemin = os.path.join(path,nomFichier)
        self.openFile()

    def openFile(self):
        # ouvre le fichier et le crée si nécessaire
        # création du self.chemin et de tous les répertoires nécessaires
        if os.path.isfile(self.chemin+'.dat') or self.flag == 'c':
            self.dictFic = shelve.open(self.chemin, self.flag)
            self.closed = False
        else:
            self.dictFic = {}
            self.close = False
            self.closed = False
        if len(self.dictFic) == 0:
            self.dictFic['dateCreation'] = str(datetime.date.today())
        if self.dictMem == {}:
            for cle, valeur in self.dictFic.items():
                self.dictMem[cle] = valeur

    def GetDict(self,dictDemande=None, groupe=None, close=True):
        """ Recupere une copie du dictionnaire demandé ds le fichier de config
            Si dictDemande est None c'est l'ensemble du groupe,
            Si groupe est None : recherché dans l'ensemble des groupes"""
        if self.closed : self.openFile()
        dictDonnees = {}
        if dictDemande == {} : dictDemande = None
        if groupe and (not (groupe in self.dictMem.keys())):
            if groupe in self.dictFic.keys():
                self.dictMem[groupe] = self.dictFic[groupe]

        def GetListKey(groupe):
            # liste des clés à Synchroniser
            # si présence d'un dictionnaire en entrée, on le met à jour sinon c'est tout le groupe
            if dictDemande:
                for key in dictDemande.keys(): self.dicKeys[key] = 0
            else :
                if groupe in self.dictMem.keys():
                    for key in self.dictMem[groupe].keys(): self.dicKeys[key] = 0
                elif groupe in self.dictFic.keys():
                    for key in self.dictFic[groupe].keys(): self.dicKeys[key] = 0

        def GetDictGroupe(groupe):
            # les données peuvent être à différents endroits : priorité au premier dictionnaire pointé
            for key in self.dicKeys:
                #recherche par priorité inversée
                if self.dicKeys[key]==0:
                    dictDonnees[key] = None
                    # valeur par défaut si non présente
                    if dictDemande:
                        if key in dictDemande.keys():
                            dictDonnees[key] = dictDemande[key]
                    self.dicKeys[key] = 1
                if self.dicKeys[key] < 2:
                    # recherche dans le deuxième dictionnaire
                    if groupe in self.dictFic:
                        #if isinstance(groupe,dict):
                            if key in self.dictFic[groupe]:
                                dictDonnees[key] = self.dictFic[groupe][key]
                                self.dicKeys[key] = 2
                if self.dicKeys[key] < 3:
                    # recherche dans le premier dictionnaire
                    if groupe in self.dictMem.keys():
                        if isinstance(self.dictMem[groupe],dict):
                            if key in self.dictMem[groupe].keys():
                                dictDonnees[key] = self.dictMem[groupe][key]
                                self.dicKeys[key] = 3

        self.dicKeys = {}
        if groupe :
            GetListKey(groupe)
            GetDictGroupe(groupe)
        else :
            for groupe in self.dictMem.keys():
                GetListKey(groupe)
                GetDictGroupe(groupe)

        return dictDonnees

    def SetDict(self,dictEnvoi=None,groupe=None, close=True, memOnly=False):
        """ Ajoute ou met à jour les clés du dictionnaire ds le fichier de config
            par défaut ce sera le groupe param si groupe est None"""
        if self.closed : self.openFile()
        if groupe and (not (groupe in self.dictMem.keys())):
            self.dictMem[groupe]={}
            if groupe in self.dictFic:
                self.dictMem[groupe] = self.dictFic[groupe]
            else: self.dictFic[groupe] = {}

        if not groupe: groupe = 'param'

        for key in dictEnvoi.keys():
            self.dictMem[groupe][key] = dictEnvoi[key]

        if not memOnly:
            # double enregistrement
            self.dictFic[groupe] = self.dictMem[groupe]
        return

    def DelDictConfig(self,cle=None,groupe=None, close=True):
        """ Supprime itemdic du fichier de config présent sur le disque """
        if self.closed : self.openFile()
        def delCle(itemdic,cle):
            for grp in itemdic.keys():
                ssdic = itemdic[grp]
                if cle in ssdic.keys():
                    del ssdic[cle]
        def delGroupe(itemdic,grp):
                if grp in itemdic:
                    del itemdic[grp]
        def delCleGroupe(itemdic,cle,grp):
                if grp in itemdic:
                    if cle in itemdic[grp]:
                        del itemdic[grp][cle]

        if hasattr(self,'dictMem'): lstDict = (self.dictMem, self.dictFic)
        else : lstDict = (self.dictFic,)

        for item in lstDict:
            itemdic = {}
            for key in item.keys():
                itemdic[key]=item[key]
            if cle and groupe:
                delCleGroupe(itemdic,cle,groupe)
            elif groupe:
                delGroupe(item,groupe)
            elif cle:
                delCle(item,cle)
            for key in item.keys():
                item[key]=itemdic[key]
        return

class ParamUser(FileShelve):
    # Gestion des paramètres dans un fichier personnel créé dans USERPROFILE
    def __init__(self, nomFichier='UserConfig', pathUser='', flag='c', close=True):
        if not pathUser:
            pathUser = GetRepUser()
        FileShelve.__init__(self, nomFichier, pathUser, flag, close)

# --------------- TESTS ----------------------------------------------------------
if __name__ == u"__main__":
    app = wx.App(0)

    reptemp = GetRepTemp()
    repshared = GetRepShared()
    repuser = GetRepUser(ajout="")

    cfgUser = ParamUser()
    cfgShared  = FileShelve(path=repshared, flag='r')

    print(len(cfgUser.dictFic), " groupes de données personnelles:")
    DumpFile(cfgUser.dictFic)
    print("\n données partagées:")
    DumpFile(cfgShared.dictFic)

