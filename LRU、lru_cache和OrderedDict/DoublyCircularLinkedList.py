import time
################################################################################
# Doubly Circular Linked List
################################################################################

PREV, NEXT, VAL = 0, 1, 2


class DoublyCircularLinkedList:

    def __init__(self) -> None:
        self.root = []
        self.root[:] = [self.root, self.root, None]

    def insert(self, val) -> None:
        '''这种实现方式从头插和从尾插是一样的，只需要一个插入方法'''
        last = self.root[PREV]
        new_node = [last, self.root, val]
        last[NEXT] = self.root[PREV] = new_node

    def delete(self) -> None:
        oldroot = self.root
        self.root = oldroot[NEXT]
        self.root[VAL] = None

    def __str__(self) -> str:
        return str(self.root)

    def test(self) -> None:
        try:
            while self.root:
                print(self.root)
                time.sleep(2)
                self.root = self.root[NEXT]
        except KeyboardInterrupt:
            print('test end')


if __name__ == '__main__':
    l = DoublyCircularLinkedList()
    l.insert(1)
    l.insert(2)
    l.insert(3)
    print(l)
    l.delete()
    l.delete()
    l.insert(4)
    l.test()
