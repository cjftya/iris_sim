from sim.iris_englne import IrisEngine

class Agent:
    def __init__(self, name="UNKNOWN", identifier="UNKNOWN"):
        self.name = name
        self.identifier = identifier
        self.llm_requester = None
        self.personality_matrix = self.get_personality_matrix()
        self.iris_engine = IrisEngine(self.name)
        self.available_participants = []

    def start(self, llm_requester):
        self.llm_requester = llm_requester

        self.iris_engine.start()
        self.iris_engine.set_llm_requester(llm_requester=self.llm_requester)
        self.iris_engine.set_personality_matrix(personality_matrix=self.get_personality_matrix())
        self.iris_engine.set_world_context(world_context=self.get_world_context())
        self.iris_engine.set_persona_context(persona_context=self.get_persona_context())
        self.iris_engine.set_response_style(response_style=self.get_response_style())

    def stop(self):
        self.llm_requester = None
        self.iris_engine.stop()
    
    def run(self, user_input):
        res = self.iris_engine.run(user_input)
        return res
    
    def get_personality_matrix(self):
        return None

    def get_persona_context(self):
        return None
    
    def get_world_context(self):
        return None

    def get_response_style(self):
        return None

    def get_available_participants(self):
        return "\n".join([line for line in self.available_participants])

    def add_participant(self, participant):
        self.available_participants.append("- **" + participant + "**")
    
    def remove_participant(self, participant):
        self.available_participants.remove("- **" + participant + "**")

    def clear_participants(self):
        self.available_participants.clear()

    def add_all_participants(self, participants):
        for participant in participants:
            self.add_participant("- **" + participant + "**")

    def set_serper_api_key(self, api_key):
        if self.iris_engine:
            self.iris_engine.set_serper_api_key(api_key)

    def set_enabled_web_search(self, enabled):
        if self.iris_engine:
            self.iris_engine.set_enabled_web_search(enabled)