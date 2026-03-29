

test = input('New Or Old? ')

if test.lower() in ['new', 'n', 'ne']:
    from Modules.GUI.Main_Menu import MainWindows
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)

    window = MainWindows()
    window.show()

    sys.exit(app.exec())
else:
    from Modules.GUI import Main_Menu_old
    menu = Main_Menu_old
