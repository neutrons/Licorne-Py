from __future__ import (absolute_import, division, print_function)
from PyQt5 import QtCore, QtWidgets, QtGui

class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        QtWidgets.QWidget.__init__(self, editor)
        self.editor = editor

    def sizeHint(self):
        return QtCore.QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class plaintexteditwithlinenumbers(QtWidgets.QPlainTextEdit):
    def __init__(self,parent):
        QtWidgets.QPlainTextEdit.__init__(self,parent)
        self.lineNumberArea = LineNumberArea(self)      
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        digits=max(1,len(str(self.blockCount())))
        return 3 + self.fontMetrics().width('9') * digits

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(),
                                       rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        QtWidgets.QPlainTextEdit.resizeEvent(self,event)
        cr = self.contentsRect();
        self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(),
                                        self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QtCore.Qt.lightGray)
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.setPen(QtCore.Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(), height,
                                 QtCore.Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def keyPressEvent(self,event):
        if (event.type() == QtCore.QEvent.KeyPress) and (event.key() == QtCore.Qt.Key_Tab):
            cursor=self.textCursor()
            cursor.insertText('    ')
        else:
            QtWidgets.QPlainTextEdit.keyPressEvent(self, event)

if __name__=='__main__':
    #This is for testing purposes only
    import sys
    app=QtWidgets.QApplication(sys.argv)
    mainForm=plaintexteditwithlinenumbers()
    mainForm.show()
    sys.exit(app.exec_())
