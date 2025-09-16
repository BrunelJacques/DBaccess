#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noexpy utilitaires,
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os
import sys
import appdirs
import wx
import tempfile
from xformat import SEP

rep = os.path.abspath(__file__)
# la racine va s'arrête au niveau 'xpy'
REP_RACINE = rep.split('%sxpy%s'%(SEP,SEP))[0]

def IsFrozen():
    return getattr(sys, 'frozen', '')

def GetRepRacine(ajout="Data"):
    """ Retourne le chemin du répertoire principal """
    return os.path.join(REP_RACINE, ajout)

def GetRepData(ajout=""):
    chemin = appdirs.user_data_dir()
    os.makedirs(chemin, exist_ok=True)
    return  os.path.join(chemin, ajout)

def GetRepTemp(ajout=""):
    chemin = tempfile.gettempdir()
    os.makedirs(chemin, exist_ok=True)
    return os.path.join(chemin, ajout)

def GetRepUser(ajout="",appname=None, roaming=False):
    chemin = appdirs.user_config_dir(appname=appname, roaming=roaming)
    os.makedirs(chemin, exist_ok=True)
    return os.path.join(chemin, ajout)


def ChoixDirFile(stdPath='local', wildcard=''):
    # options possibles répertoire par défaut
    dir = ''
    if stdPath != 'local':
        sp = wx.StandardPaths.Get()
        if stdPath == 'doc':
            dir = sp.GetDocumentsDir()
        elif stdPath == 'src':
            dir = sp.GetConfigDir()
        elif stdPath == 'temp':
            dir = sp.GetTempDir
        elif stdPath == 'roaming':
            dir = sp.GetConfigDir
    else:
        dir = GetRepUser()

    # options filtrage des fichiers
    if not wildcard:
        exc = "Excel files (*.xls;*.xlsx)|*.xls;*.xlsx"
        txt = "CSV files (*.csv)|*.csv|Text files (*.txt)|*.txt"
        all = "All files (*.*)|*.*"
        wildcard = '|'.join((exc,txt,all))

    # Demande à l'utilisateur un répertoire
    dlg = wx.FileDialog(
        None, message="Veuillez sélectionner un répertoire et saisir un nom de fichier",
        defaultDir = dir,
        style=wx.FD_SAVE,
        wildcard = wildcard
    )
    dlg.SetFilterIndex(0)
    if dlg.ShowModal() == wx.ID_OK:
        dir = dlg.GetDirectory()
        file = dlg.GetFilename()
    else:
        dir, file = '',''
    dlg.Destroy()
    return dir,file




if __name__ == "__main__":
    # Répertoires via os
    print('GetRepRacine:',GetRepRacine(),)
    print('GetRepUser:',GetRepUser(),)
    print('GetRepData:',GetRepData(),)
    print('GetRepTemp:',GetRepTemp(),)

    # Repertoires via wx.StandardPaths
    app = wx.App(0)
    os.chdir("..")
    os.chdir("..")
    std_paths = wx.StandardPaths.Get() # Appelle les répertoires
    print(' std_paths.GetAppDocumentsDir',
          std_paths.GetAppDocumentsDir())  # Return the directory for the document files used by this application.
    print(' std_paths.GetConfigDir',
          std_paths.GetConfigDir())  # Return the directory containing the system config files.
    print(' std_paths.GetDocumentsDir',
          std_paths.GetDocumentsDir())  # Same as calling GetUserDir with Dir_Documents parameter.
    print(' std_paths.GetTempDir',
          std_paths.GetTempDir())  # Return the directory for storing temporary files, for the current user.
    print(' std_paths.GetUserConfigDir',
          std_paths.GetUserConfigDir())  # Return the directory for the user config files.
    print(ChoixDirFile())
