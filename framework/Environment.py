
class Local_Field:
    def __init__(self, b, k = 0):
        self.b = b
        self.k = k
        self.field = b

    def sense(self, time):
        return self.b + self.k * time

class Environment:
    def __init__(self, field_para: list):
        self.local_fields = []
        for n in field_para:
            self.local_fields.append(Local_Field(n[0], n[1]))

    def sense(self, node_id, time) -> float:
        return self.local_fields[node_id].sense(time)

    def field(self, time):
        return [self.local_fields[i].sense(time) for i in range(len(self.local_fields))]


