import wx
import pyodbc
from xpy.xDB import DB, GetConfigs,GetOneConfig

class Dialog(wx.Panel):

    def __init__(self, parent):
        super().__init__(parent)

        # scan environnement
        """
        print(pyodbc.drivers()) # perme de déterminer la version
        print(GetConfigs())
        print(GetOneConfig('quadra'))"""

        self.InitDB()
        self.Action()


    def InitDB(self):
        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb)};'
            r'DBQ=D:\Quadra\Database\cpta\DC\MATTH\qcompta.mdb'
        )
        conn = pyodbc.connect(conn_str)
        self.cursor = conn.cursor()
        # affiche toutes les tables
        for i in self.cursor.tables(tableType='TABLE'):
            print(i.table_name)
        # affiche les vues
        for i in self.cursor.tables(tableType='VIEW'):
            print(i.table_name)


    def Action(self):
        self.db = DB(nomFichier=r"D:\Quadra\Database\cpta\DC\MATTH\qcompta.mdb")
        self.db.AfficheTestOuverture()
        cursor =self.cursor
        # --------------------  SQL  ------------------------
        myTable = "Ecritures"
        req = f"""SELECT * 
            FROM  {myTable}
            WHERE NumeroCompte = '75400000'
            """


        cursor.execute(req)
        lstCol = [ x[0] for x in cursor.description ]
        print(lstCol)

        records = cursor.fetchall()
        for ligne in records:
            print(ligne[:15])

        cursor.close()
        self.InitDB()
        cursor = self.cursor
        cursor.execute(req)
        print("troisième",cursor.fetchone())


if __name__ == '__main__':
    import os
    os.chdir("..")
    os.chdir("..")


    app = wx.App(0)
    dlg = wx.Dialog(None,-1,"Dialog Test")
    dlg.pnl = Dialog(dlg)
    app.SetTopWindow(dlg)
    ret = dlg.ShowModal()
    app.MainLoop()