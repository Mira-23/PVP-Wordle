class Protocols:
    class Response:
        NICKNAME = "protocol.request_nickname"
        QUESTIONS = "protocol.questions" # should be changed
        START = "protocol.start"
        OPPONENT = "protocol.opponent"
        OPPONENT_ADVANCE = 'protocol.opponent_advance'
        ANSWER_VALID = "protocol.answer_valid"
        ANSWER_INVALID = 'protocol.answer_invalid' # should be removed
        WINNER = "protocol.winner"
        OPPONENT_LEFT = "protocol.opponent_left"

    class Request:
        ANSWER = "protocol.answer"
        NICKNAME = "protocol.send_nickname"
        LEAVE = "protocol.leave"