#include <functional>
#include <iostream>
#include <list>
#include <queue>
#include <tuple>
#include <unordered_map>

class LRUCache {
   private:
    std::unordered_map<int, std::list<std::pair<int, int>>::iterator> mp;
    std::list<std::pair<int, int>> data;
    int cap;

    void remove(std::list<std::pair<int, int>>::iterator it)
    {
        mp.erase(it->first);
        data.erase(it);
    }

    void update(int key, int val)
    {
        data.push_front({key, val});
        mp[key] = data.begin();
    }

   public:
    LRUCache(int capacity) : cap(capacity) {}

    int get(int key)
    {
        int val = -1;
        if (mp.find(key) != mp.end()) {
            val = mp[key]->second;
            data.erase(mp[key]);
            this->update(key, val);
        }
        return val;
    }

    void put(int key, int value)
    {
        if (mp.find(key) != mp.end()) data.erase(mp[key]);
        this->update(key, value);
        if (data.size() > cap) this->remove(std::prev(data.end()));
    }
};