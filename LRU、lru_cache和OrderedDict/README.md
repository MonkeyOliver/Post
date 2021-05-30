# LRU、lru_cache和OrderedDict

## LRU Cache

在实现LRU Cache之前首先我们要搞清楚啥是LRU，LRU全称Least recently used，从名字直译出来就是“最少最近使用”，但要真按顺序想就错了，事实上我一开始就按顺序想的，然而学习了一下具体实现后发现其实LRU真正的侧重点其实是recently，即最近，这应该算是个中英文翻译理解上的问题，所以其实LRU缓存首先弹出的是最**远**使用过的key，即使一个key连续用了100次，第101次用的另一个key，第102次要弹出key的时候也会优先弹出之前那个用了100次的key，即使它之前被用了100次，因为它不是“最近”使用的key。

搞明白啥是LRU后实现思路就非常简单了，整一个双向链表（因为要进行O1的首尾操作）存key和value，再整一个哈希表存key和key在链表中的位置pos（通过哈希表达到O1查询），然后主要有两个核心操作，put和get，就搞完了，具体来讲是这样：

### put(key, value)

向缓存中插入一个新键值对，即：

- 如果哈希表中有key，拿到对应的pos更新链表中key对应的value，再将对应键值对挪到链表**头部**
- 如果哈希表中没有key，
  - 缓存没满，直接插入链表头部。
  - 缓存满了，弹出链表**尾巴**键值对和哈希表中该键值对对应的key，将新键值对插入链表**头部**。

以上所有操作时间复杂度O1

### get(key)

获取缓存中key所对应的值，即在哈希表中看看有没有key，如果不存在返回-1，否则根据哈希表拿到key在链表中的位置pos，再根据pos在链表中找到key对应的value，最后别忘了把链表中这个key所对应的键值对挪到**头部**。以上所有操作时间复杂度也是O1。

最后就可以快乐地A掉[leetcode146](https://leetcode.com/problems/lru-cache/)了。

    class LRUCache {
       private:
        std::unordered_map<int, std::list<std::pair<int, int>>::iterator> mp;
        std::list<std::pair<int, int>> data;
        int cap;

        void remove(std::list<std::pair<int, int>>::iterator it) {
            mp.erase(it->first);
            data.erase(it);
        }

        void update(int key, int val) {
            data.push_front({key, val});
            mp[key] = data.begin(); //别忘了哈希表中存的是迭代器
        }

       public:
        LRUCache(int capacity) : cap(capacity) {}

        int get(int key) {
            int val = -1;
            if (mp.find(key) != mp.end()) {
                val = mp[key]->second;
                data.erase(mp[key]);
                this->update(key, val);
            }
            return val;
        }

        void put(int key, int value) {
            if (mp.find(key) != mp.end()) data.erase(mp[key]);
            this->update(key, value);
            if (data.size() > cap) this->remove(std::prev(data.end()));
        }
    };

## functools.lru_cache

然后我们来看看Python标准库中functools.lru_cache具体是怎么实现的，和刚才那道题不同，Python实现lru_cache使用了双向**循环**链表，这样可以避免考虑头部尾部，只需要对一个位置的节点进行操作。

### 双向循环链表

其实就是双向链表再加一个尾巴指向头部和头部指向尾部的指针，不过直接用强引用指针会出现一个循环引用的问题，一般解决方法是一个方向全用强引用指针，而反向使用不会增加引用计数的弱引用指针，但！是！在lru_cache里双向循环链表并没有考虑循环引用的问题而直接用了这么一种实现（我把lru_cache中双向循环链表的实现Parse出来后又封装了一些操作）：

    PREV, NEXT, VAL = 0, 1, 2

    class DoublyCircularLinkedList:

        def __init__(self) -> None:
            self.root = []
            self.root[:] = [self.root, self.root, None]

        def insert(self, val) -> None:
            last = self.root[PREV]
            new_node = [last, self.root, val]
            last[NEXT] = self.root[PREV] = new_node

        def delete(self) -> None:
            oldroot = self.root
            self.root = oldroot[NEXT]
            self.root[VAL] = None

        def __str__(self) -> str:
            return str(self.root)

可以试着用[Python Tutor](http://pythontutor.com/)跑一跑上面这个代码，会发现确实会产生循环引用的问题，于是我接下来在[Python bug tracker](https://bugs.python.org)上搜了搜，果然在2013年的[issue19859](https://bugs.python.org/issue19859)中有人提到了这个问题，具体讨论有兴趣的朋友自己去看吧，反正最后得出的结论是：

> Every container (except for the weakref containers) keeps their references alive. That is how Python works. The LRU cache is no more special in this regard than a dictionary, list, or set. In addition, the older entries get flushed-out and freed as the LRU cache gets newer entries.

双向循环链表的问题解决后lru_cache基本就一目了然了，接下来简单地在源码里添点儿注释，lru_cache的注释其实写得挺详细，所以有详细英文注释的地方就不再赘述了。

### 参数校验

主要是对maxsize和type的类型和值进行校验，以及如果不是以装饰器形式调用lru_cache的话进行一个转换

    if isinstance(maxsize, int):
        # Negative maxsize is treated as 0
        if maxsize < 0:
            maxsize = 0
    elif callable(maxsize) and isinstance(typed, bool):
        # The user_function was passed in directly via the maxsize argument 如果直接将function传入，默认将maxsize设为128
        user_function, maxsize = maxsize, 128
        wrapper = _lru_cache_wrapper(user_function, maxsize, typed, _CacheInfo)
        return update_wrapper(wrapper, user_function)
    elif maxsize is not None:
        raise TypeError(
            'Expected first argument to be an integer, a callable, or None')

### _lru_cache_wrapper

#### 用到的变量

    # Constants shared by all lru cache instances:
    sentinel = object()          # unique object used to signal cache misses
    make_key = _make_key         # build a key from the function arguments 用来形成缓存中的键
    PREV, NEXT, KEY, RESULT = 0, 1, 2, 3   # names for the link fields 给双向循环链表中的下标起个名字

    cache = {} # 哈希表部分直接用了内置字典
    hits = misses = 0 # 记录缓存信息
    full = False # 判断缓存是否已满
    cache_get = cache.get    # bound method to lookup a key or return None
    cache_len = cache.__len__  # get cache size without calling len()
    lock = RLock()           # because linkedlist updates aren't threadsafe
    root = []                # root of the circular doubly linked list # 双向循环链表由列表实现
    root[:] = [root, root, None, None]     # initialize by pointing to self

#### maxsize为0，不缓存

不缓存那就跟直接调用函数效果相同

    def wrapper(*args, **kwds):
        # No caching -- just a statistics update
        nonlocal misses
        misses += 1
        result = user_function(*args, **kwds)
        return result

#### maxsize为None，缓存无限大

缓存无限大其实就是把所有键值对都塞到字典里

    def wrapper(*args, **kwds):
        # Simple caching without ordering or size limit
        nonlocal hits, misses
        key = make_key(args, kwds, typed)
        result = cache_get(key, sentinel)
        if result is not sentinel:
            hits += 1
            return result
        misses += 1
        result = user_function(*args, **kwds)
        cache[key] = result
        return result

#### maxsize固定，真正意义上的lru缓存

    def wrapper(*args, **kwds):
        # Size limited caching that tracks accesses by recency
        nonlocal root, hits, misses, full
        key = make_key(args, kwds, typed) # 哈希化user_function的参数并做一个key
        with lock: # 加锁
            link = cache_get(key) 从缓存中获取一下
            if link is not None:
                # 如果获取到了，把获取到的link节点挪到双向循环链表头部
                # Move the link to the front of the circular queue
                link_prev, link_next, _key, result = link
                link_prev[NEXT] = link_next
                link_next[PREV] = link_prev
                last = root[PREV]
                last[NEXT] = root[PREV] = link
                link[PREV] = last
                link[NEXT] = root
                hits += 1
                return result # 将缓存中获取到的值直接返回
            misses += 1 # 如果没在cache中获取到link，递增miss数
        result = user_function(*args, **kwds) # 只有没在缓存中获取到result才会走到这一步，否则上面就返回了
        with lock: # 加锁
            if key in cache:
                # Getting here means that this same key was added to the
                # cache while the lock was released.  Since the link
                # update is already done, we need only return the
                # computed result and update the count of misses.
                pass
            elif full:
                # 如果缓存满了，根据lru的规则进行淘汰，即淘汰双向循环链表尾部节点
                # Use the old root to store the new key and result.
                oldroot = root
                oldroot[KEY] = key
                oldroot[RESULT] = result
                # Empty the oldest link and make it the new root.
                # Keep a reference to the old key and old result to
                # prevent their ref counts from going to zero during the
                # update. That will prevent potentially arbitrary object
                # clean-up code (i.e. __del__) from running while we're
                # still adjusting the links.
                root = oldroot[NEXT]
                oldkey = root[KEY]
                oldresult = root[RESULT]
                root[KEY] = root[RESULT] = None
                # Now update the cache dictionary.
                del cache[oldkey]
                # Save the potentially reentrant cache[key] assignment
                # for last, after the root and links have been put in
                # a consistent state.
                cache[key] = oldroot
            else:
                # Put result in a new link at the front of the queue.
                last = root[PREV]
                link = [last, root, key, result]
                last[NEXT] = root[PREV] = cache[key] = link
                # Use the cache_len bound method instead of the len() function
                # which could potentially be wrapped in an lru_cache itself.
                full = (cache_len() >= maxsize)
        return result

然后如果你用Python刷过题的话很有可能意识到这玩意儿可以拿来做记忆化搜索，记忆化搜索是用数组存值，lru_cache用字典存值而已，本质上都是哈希一下状态再次遇到同样状态时直接通过哈希表查，比如说[洛谷P1464](https://www.luogu.com.cn/problem/P1464)，正解是记忆化搜索，但用了lru_cache题解就变成了**直接翻译题目**即可：

    from functools import lru_cache

    @lru_cache(None)
    def w(a, b, c):
        if a <= 0 or b <= 0 or c <= 0:
            return 1
        elif a > 20 or b > 20 or c > 20:
            return w(20, 20, 20)
        elif a < b < c:
            return w(a, b, c-1)+w(a, b-1, c-1)-w(a, b-1, c)
        else:
            return w(a-1, b, c)+w(a-1, b-1, c)+w(a-1, b, c-1)-w(a-1, b-1, c-1)


    if __name__ == '__main__':
        while True:
            s = input()
            s = [int(i) for i in s.split()]
            if s[0] == -1 and s[1] == -1 and s[2] == -1:
                break
            print('w(%s, %s, %s) = %s' % (s[0], s[1], s[2], w(s[0], s[1], s[2])))

## collections.OrderedDict

那么最后一部分，这篇文章主要讲的lru_cache怎么会扯到OrderedDict上呢？因为事实上OrderedDict的实现和lru_cache几乎是一模一样，也是一个双向循环链表+一个字典，并且有意思的是在Python2中OrderedDict用的是那个有循环引用问题的双向循环链表，而到Python3的时候就换成了用弱引用指针的双向循环链表，然后官方文档里也举了一个用OrderedDict实现lru_cache的例子

    class LRU(OrderedDict):
        'Limit size, evicting the least recently looked-up key when full'

        def __init__(self, maxsize=128, /, *args, **kwds):
            self.maxsize = maxsize
            super().__init__(*args, **kwds)

        def __getitem__(self, key):
            value = super().__getitem__(key)
            self.move_to_end(key)
            return value

        def __setitem__(self, key, value):
            if key in self:
                self.move_to_end(key)
            super().__setitem__(key, value)
            if len(self) > self.maxsize:
                oldest = next(iter(self))
                del self[oldest]

看起来貌似就简单了许多。（虽然方法名字叫move_to_end，但实际上对于循环链表来说移动到哪一端都行）

## 参考链接

[Rust双向链表分析之旅](http://raindust.xyz/post/2020/rust_double_linked_list/)

[使用gc、objgraph干掉python内存泄露与循环引用！](https://www.cnblogs.com/xybaby/p/7491656.html)

[functools.lru_cache keeps objects alive forever](https://bugs.python.org/issue19859)

[functools --- 高阶函数和可调用对象上的操作](https://docs.python.org/zh-cn/3/library/functools.html)

[OrderedDict 对象](https://docs.python.org/zh-cn/3/library/collections.html#ordereddict-objects)

《Fluent Python》第二版