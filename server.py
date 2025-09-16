import wx
import pyodbc
from xpy.xDB import DB, GetConfigs,GetOneConfig

class Dialog(wx.Panel):

    def __init__(self, parent):
        super().__init__(parent)

        # scan environnement
        print(pyodbc.drivers()) # perme de déterminer la version
        print(GetConfigs())
        print(GetOneConfig('quadra'))
        self.InitDB()



    def InitDB(self):
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb)};'
            r'DBQ=D:\Quadra\Database\cpta\DC\MATTH\qcompta.mdb'
        )
        self.connexion = pyodbc.connect(conn_str)
        self.cursor = self.connexion.cursor()
        # affiche toutes les tables
        for i in self.cursor.tables(tableType='TABLE'):
            print(i.table_name)
        # affiche les vues
        for i in self.cursor.tables(tableType='VIEW'):
            print(i.table_name)


    def Action(self):
        self.db = DB()
        self.db.AfficheTestOuverture()
        cursor =self.cursor
        # --------------------  SQL  ------------------------
        myTable = "Ecritures"
        req = f"""SELECT * FROM  {myTable}"""
        cursor.execute(req)
        lstCol = [ x[0] for x in cursor.description ]
        print(lstCol)
        print("premier",cursor.fetchone())
        print("deuxième",cursor.fetchone())
        records = cursor.fetchall()
        cursor.close()
        cursor = self.connexion.cursor()
        cursor.execute(req)
        print("troisième",cursor.fetchone())


if __name__ == '__main__':

    app = wx.App(0)
    dlg = wx.Dialog(None,-1,"Dialog Test")
    dlg.pnl = Dialog(dlg)
    app.SetTopWindow(dlg)
    ret = dlg.ShowModal()
    app.MainLoop()