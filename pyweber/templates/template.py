import os
import re

class Element:
    def __init__(
        self,
        name: str,
        id: str = None,
        class_name: str = None,
        content: str = None,
        attributes: dict[str, str] = None,
        parent: 'Element' = None,
        childs: list['Element'] = None
    ):
        self.name = name
        self.id = id
        self.class_name = class_name
        self.content = content
        self.attributes = attributes if attributes else {}
        self.parent = parent
        self.childs = childs if childs else []
    
    def __repr__(self):
        return f"Element(name={self.name}, id={self.id}, class_name={self.class_name}, content={self.content}, attributes={self.attributes}, childs={len(self.childs)})"
        
class Template:
    def __init__(self, template: str):
        self.template = template
        self.__root = self.parse
    
    @property
    def read_file(self):
        if self.template.endswith('.html'):
            path = os.path.join('templates', self.template)
            if os.path.exists(path):
                with open(os.path.join('templates', self.template), 'r', encoding='utf-8') as file:
                    return file.read()
            
            raise FileNotFoundError('O ficheiro não existe! Inclua na pasta ./templates')

        return f"<html><head></head><body>{self.template.strip()}</body></html>"
    
    @property
    def parse(self) -> Element:
        html = self.read_file
        root = self.__parse_html(html)
        return root

    @property
    def root(self) -> Element:
        return self.__root
    
    @root.setter
    def root(self, new_element: Element):
        if isinstance(new_element, Element):
            self.__root = new_element
        
        else:
            raise TypeError(f'O tipo não deve ser {type(new_element)}')
    
    def merge_templates(self, new: Element, old: Element):
        def merge(new_elem: Element, old_elem: Element):
            if old_elem.content:
                new_elem.content = old_elem.content
            for old_child in old_elem.childs:
                new_child = next((child for child in new_elem.childs if child.name == old_child.name), None)
                if new_child:
                    merge(new_child, old_child)
                else:
                    new_elem.childs.append(old_child)
        
        merge(new, old)

        return new

    def __parse_html(self, html: str) -> Element:
        tag_pattern = re.compile(r'<(\w+)([^>]*)>(.*?)<\/\1>|<(\w+)([^>]*?)\s*\/?>', re.DOTALL)

        elements: list[Element] = []

        for match in tag_pattern.finditer(html):
            if match.group(1):  # Tag com fechamento
                name = match.group(1)
                tag_attributes = match.group(2)
                inner_html = match.group(3).strip()

                attributes = self.__parse_attributes(tag_attributes)
                element = Element(
                    name=name,
                    class_name=attributes.pop('class', None),
                    id=attributes.pop('id', None),
                    attributes=attributes,
                )

                if inner_html:
                    if not re.search(r'<[^>]+>', inner_html):  
                        element.content = inner_html
                    else:
                        child_elements = self.__parse_html(inner_html)

                        if isinstance(child_elements, list):  # Se houver múltiplos elementos
                            element.childs.extend(child_elements)
                            for child in child_elements:
                                child.parent = element
                        
                        else:
                            element.childs.append(child_elements)
                            child_elements.parent = element  # Definir parent corretamente

            else:  # Tag auto-fechada
                name = match.group(4)
                tag_attributes = match.group(5)

                attributes = self.__parse_attributes(tag_attributes)
                element = Element(
                    name=name,
                    class_name=attributes.pop('class', None),
                    id=attributes.pop('id', None),
                    attributes={key: (True if value is None else value) for key, value in attributes.items()}
                )

            elements.append(element)

        # Criar um nó raiz se houver vários elementos principais
        if len(elements) == 1:
            return elements[0]
        elif elements:
            return elements  # Retorna a lista diretamente se houver múltiplos elementos
        else:
            raise ValueError("No elements found in the HTML")


    def __parse_attributes(self, tag_attributes: str) -> dict:
        attributes = {}
        attr_pattern = re.compile(r'(\w+)=["\']([^"\']*)["\']')

        for attr_match in attr_pattern.finditer(tag_attributes):
            key = attr_match.group(1)
            value = attr_match.group(2)
            attributes[key] = value
        return attributes

    def __build_html(self, element: Element, indent_level: int = 0) -> str:
        indent = " " * indent_level * 4  # 4 espaços por nível de indentação
        html = f"{indent}<{element.name}"

        # inserindo as tags class_name e id caso existam
        if element.id:
            html += f' id="{element.id}"'
        if element.class_name:
            html += f' class="{element.class_name}"'

        # Adiciona os atributos
        if element.attributes:
            for key, value in element.attributes.items():
                html += f' {key}="{value}"' if not isinstance(value, bool) else f' {key}'

        # Se for uma tag auto-fechada e não tem filhos ou conteúdo
        if not element.content and not element.childs:
            html += ">\n"
        else:
            html += ">\n"

            # Adiciona o conteúdo (se houver)
            if element.content:
                html += f"{indent}    {element.content.strip()}\n"

            # Adiciona os filhos (recursivamente)
            for child in element.childs:
                html += self.__build_html(child, indent_level + 1)

            # Fecha a tag corretamente
            html += f"{indent}</{element.name}>\n"

        return html

    @property
    def rebuild_html(self) -> str:
        # Adiciona o DOCTYPE e constrói o HTML a partir do elemento raiz
        return f"<!DOCTYPE html>\n{self.__build_html(self.__root)}"
    
    def getElementById(self, id: str) -> Element | None:
        def search(element: Element):
            if element.id == id:
                return element
            for child in element.childs:
                found = search(child)
                if found:
                    return found
            return None
        return search(self.__root)
    
    def getElementByClass(self, class_name: str) -> list[Element]:
        def search(element: Element, results: list[Element]):
            if class_name in (element.class_name or "").split():
                results.append(element)
            for child in element.childs:
                search(child, results)
            return results
        return search(self.__root, [])
    
    def querySelectorAll(self, tag: str) -> list[Element]:
        def search(element: Element, results: list[Element]):
            if element.name == tag:
                results.append(element)
            for child in element.childs:
                search(child, results)
            return results
        return search(self.__root, [])
    
    def querySelector(self, tag: str) -> Element | None:
        def search(element: Element):
            if element.name == tag:
                return element
            for child in element.childs:
                result = search(child)
                if result:
                    return result
            return None
        return search(self.__root)
    
    def find_parent(self, element: Element) -> Element | None:
        return element.parent