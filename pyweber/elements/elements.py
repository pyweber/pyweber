import json
import uuid as UUID
from pyweber.globals.globals import MODIFIED_ELEMENTS

class Element:
    def __init__(
        self,
        name: str,
        id: str = None,
        class_name: str = None,
        content: str = None,
        value: str = None,
        attributes: dict[str, str] = None,
        parent: 'Element' = None,
        childs: list['Element'] = None,
        events: dict[str, str] = None,
        uuid: str = None
    ):
        self._initializing = True
        self.name = name
        self.id = id
        self.uuid = uuid or str(UUID.uuid4())
        self.class_name = class_name
        self.content = content
        self.value = value
        self.attributes = attributes if attributes else {}
        self.parent = parent
        self.childs = ObservableList(self, childs if childs else [])
        self.events = events if events else {}
        self._initializing = False
    
    def __setattr__(self, name, value):
        self.__dict__[name] = value

        if name in ["name", "id", "uuid", "class_name", "content", "value", "attributes", "events"]:
            if name in self.__dict__ and self.__dict__[name] == value:
                return
        
        if not getattr(self, '_initializing', False) and name in self.__dict__ and name != '_initializing':
            MODIFIED_ELEMENTS[self.uuid] = self
    
    def __repr__(self):
        return f"Element(name={self.name}, id={self.id}, uuid={self.uuid}, class_name={self.class_name}, content={self.content}, attributes={self.attributes}, childs={len(self.childs)})"
    
    @classmethod
    def from_json(cls, data: dict, parent_map: dict[str, 'Element'] = {}):
        """
        Cria um objeto Element a partir de um dicionário (JSON decodificado).
        """
        if not isinstance(data, dict):
            raise ValueError("Os dados devem ser um dicionário JSON válido.")

        element = cls(
            name=data.get("name"),
            id=data.get("id", None),
            uuid=data.get("uuid", str(UUID.uuid4())),
            class_name=data.get("class_name", None),
            content=data.get("content", None),
            value=data.get('value', None),
            attributes=data.get("attributes", {}),
            parent=None,
            childs=[cls.from_json(child) for child in data.get("childs", [])],
            events=data.get("events", {})
        )

        if parent_map is not None:
            parent_map[element.uuid] = element

        # Desserializa os filhos
        for child_data in data.get("childs", []):
            child = cls.from_json(child_data, parent_map)
            child.parent = element
            element.childs.append(child)

        # Define o parent do elemento (se houver)
        if data.get("parent_uuid") and parent_map is not None:
            element.parent = parent_map.get(data["parent_uuid"])

        return element
    
    def to_json(self):
        """
        Converte o objeto Element para um dicionário JSON.
        """
        return {
            "name": self.name,
            "id": self.id,
            "uuid": self.uuid,
            "class_name": self.class_name,
            "content": self.content,
            "value": self.value,
            "attributes": self.attributes,
            "events": self.events,
            "parent_uuid": self.parent.uuid if self.parent else None,
            "childs": [child.to_json() for child in self.childs]
        }

    def to_json_str(self):
        """
        Retorna a versão JSON em formato de string.
        """
        return json.dumps(self.to_json(), ensure_ascii=False, indent=4)


class ObservableList(list):
    def __init__(self, parent: Element, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

    def append(self, item):
        super().append(item)
        item.parent = self.parent
        MODIFIED_ELEMENTS[self.parent.uuid] = self.parent

    def extend(self, items):
        super().extend(items)
        for item in items:
            item.parent = self.parent
        
        MODIFIED_ELEMENTS[self.parent.uuid] = self.parent

    def remove(self, item):
        super().remove(item)
        item.parent = None
        MODIFIED_ELEMENTS[self.parent.uuid] = self.parent
    
    def pop(self, index = -1):
        item = super().pop(index)
        item.parent = None
        MODIFIED_ELEMENTS[self.parent.uuid] = self.parent
    
    def clear(self):
        for item in self:
            item.parent = None
        
        MODIFIED_ELEMENTS[self.parent.uuid] = self.parent