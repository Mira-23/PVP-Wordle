class Room:
    def __init__(self, client1, client2):
        self.questions, self.answers = self.generate_questions()
        self.indexes = {client1:0,client2: 0}
        self.finished = False

    #change
    def generate_questions(self):
        return ["a","b","c"], [1,2,3]
    #change
    def verify_answer(self,client,attempt):
        if self.finished:
            return False
        
        index = self.indexes[client]
        answer = self.answers[index]
        correct = answer == attempt

        if correct:
            self.indexes[client]+=1

        return correct