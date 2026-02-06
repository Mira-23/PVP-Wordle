class Protocols:
    class Response:
        NICKNAME = "protocol.request_nickname"
        GUESSES = "protocol.guesses"
        START = "protocol.start"
        OPPONENT = "protocol.opponent"
        OPPONENT_ADVANCE = 'protocol.opponent_advance'
        ANSWER_VALID = "protocol.answer_valid"
        ANSWER_INVALID = 'protocol.answer_invalid' # should be removed
        WINNER = "protocol.winner"
        OPPONENT_LEFT = "protocol.opponent_left"
        NEW_ROUND = "protocol.new_round"
        SETTINGS = "protocol.settings"

    class Request:
        ANSWER = "protocol.answer"
        NICKNAME = "protocol.send_nickname"
        LEAVE = "protocol.leave"
        JOIN_GAME = "protocol.join_game"
        CREATE_GAME = "protocol.create_game"