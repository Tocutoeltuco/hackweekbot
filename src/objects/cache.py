import asyncio

class Cache:
	maxsize = 1
	cursize = 0
	cached = {}

	def append(self, name, args, value):
		self.cursize += 1

		while self.cursize > self.maxsize:
			lower, val = None, None
			
			for func, cache in self.cached.items():
				for arg, data in cache.items():
					if (lower is None) or (data[0] < lower):
						lower = data[0]
						val = [func, arg]

			if val is None:
				raise ValueError("Cache.maxsize can't be 0.")

			self.remove(*val)

		if name not in self.cached:
			self.cached[name] = {}
		if args not in self.cached[name]:
			self.cached[name][args] = None
		self.cached[name][args] = [0, value]

	def remove(self, name, args):
		if name in self.cached:
			if args in self.cached[name]:
				del self.cached[name][args]
				self.cursize -= 1

			if len(self.cached[name]) == 0:
				del self.cached[name]

	def get_from_cache(self, name, args):
		if (name not in self.cached) or (args not in self.cached[name]):
			return (False,)

		self.cached[name][args][0] += 1
		return True, self.cached[name][args][1]

	def cache(self, func):
		name = func.__name__

		if asyncio.iscoroutinefunction(func):
			async def wrapper(*args, **kwargs):
				data = self.get_from_cache(name, args)

				if not data[0]:
					self.append(name, args, await func(*args, **kwargs))
					return self.get_from_cache(name, args)[1]
				return data[1]

		else:
			def wrapper(*args, **kwargs):
				data = self.get_from_cache(name, args)

				if not data[0]:
					self.append(name, args, func(*args, **kwargs))
					return self.get_from_cache(name, args)[1]
				return data[1]

		wrapper.__name__ = name
		return wrapper