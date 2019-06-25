import aiomysql

class Database:
	def __init__(self, host, port, user, password, db, maxsize, loop=None):
		self.loop = loop
		self.host, self.port, self.user, self.password, self.db = host, port, user, password, db
		self.maxsize = maxsize
		self.pool = None

	async def initialize(self):
		self.pool = await aiomysql.create_pool(
			host=self.host, port=self.port, user=self.user,
			password=self.password, db=self.db, autocommit=True, minsize=0,
			maxsize=self.maxsize, loop=self.loop
		)

	async def query(self, query, *params, fetch="all"):
		result = None
		if self.pool is None:
			await self.initialize()

		async with self.pool.acquire() as connection:
			async with connection.acquire() as cursor:
				await cursor.execute(query, args=(params if len(params) > 0 else None))

				if fetch == "all":
					result = await cursor.fetchall()

				else:
					result = await cursor.fetchone()

		if fetch == "all" and len(result) == 0:
			return None
		return result