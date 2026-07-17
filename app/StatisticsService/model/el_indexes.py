from .el_connect import elastic_client as es
from ..set.settings import SELECTION_INDEX, RECOGNITION_INDEX


def create_selection_index():
    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "default": {
                        "type": "russian"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                # --- Базовые поля (обязательные) ---
                "product_id": {"type": "keyword"},  # keyword — для точного поиска и агрегаций
                "user_id": {"type": "keyword"},
                "date_search": {
                    "type": "date",
                    "format": "dd.MM.yyyy HH:mm:ss||strict_date_optional_time"
                },

                # --- Информация о продукте ---
                "product_name": {
                    "type": "text",
                    "analyzer": "russian",  # русский стеммер/лемматизация
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256}  # для сортировки/агрегаций
                    }
                },
                "product_description": {
                    "type": "text",
                    "analyzer": "russian",
                    "copy_to": "full_text"  # см. ниже
                },
                "product_manufacturer": {
                    "type": "keyword"
                },
                "product_image_url": {
                    "type": "keyword"
                },
                "product_created_at": {
                    "type": "date",
                    "format": "date_time"
                },

                # --- Информация о пользователе ---
                "user_uuid": {"type": "keyword"},
                "user_fio": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
                },
                "user_email": {"type": "keyword"},
                "user_directorate": {"type": "keyword"},  # напр. "Дирекция по маркетингу"
                "user_work_position": {"type": "keyword"},  # "Программист"
                "user_office": {"type": "long"},
                "user_department": {"type": "keyword"},  # "Отдел WEB-маркетинга"
                "user_work_city": {"type": "keyword"},  # "Саратов"
                "user_work_phone": {"type": "keyword"},  # телефон может содержать '5219' или "+7 (999) 123-45-67"
                "document_number": {"type": "long"},
                "status": {"type": "keyword"},  # выполнен или нет
                # --- Доп. поля для полнотекстового поиска ---
                # "full_text": {
                #     "type": "text",
                #     "analyzer": "russian",
                #     "fields": {
                #         "trigram": {
                #             "type": "text",
                #             "analyzer": "trigram_analyzer"
                #         }
                #     }
                # },

                # --- Параметры из selection_json ---
                # Используем dynamic: true для гибкости, но задаём шаблоны
                "parameters": {
                    "type": "object",
                    "dynamic": True
                }
            },
            "dynamic_templates": [
                # 1. long_* → тип long (например, "long_123")
                {
                    "longs_as_strings": {
                        "path_match": "parameters.long_*",
                        "mapping": {"type": "long"}
                    }
                },
                # 2. *_text → text (например, "product_text")
                {
                    "strings_as_text": {
                        "path_match": "parameters.*_text",
                        "mapping": {"type": "text", "analyzer": "russian"}
                    }
                },
                # 3. Другие строки → keyword (для точного поиска)
                {
                    "strings_as_keywords": {
                        "path_match": "parameters.*",
                        "match_mapping_type": "string",
                        "mapping": {"type": "keyword"}
                    }
                },
                # 4. Массивы строк → keyword[] (если не указано иное)
                {
                    "arrays_of_strings": {
                        "path_match": "parameters.*",
                        "match_mapping_type": "string",
                        "mapping": {"type": "keyword"}
                    }
                },
                # 5. Числа (float/int) → double/long
                {
                    "numbers_as_double": {
                        "path_match": "parameters.*",
                        "match_mapping_type": "double",
                        "mapping": {"type": "double"}
                    }
                },
                {
                    "numbers_as_long": {
                        "path_match": "parameters.*",
                        "match_mapping_type": "long",
                        "mapping": {"type": "long"}
                    }
                }
            ]
        }
    }
    
    if not es.indices.exists(index=SELECTION_INDEX):
        # Создаём альтернативный анализатор для partial match (опционально)
        es.indices.create(
            index=SELECTION_INDEX,
            body=mapping
        )
    return True

def create_recognition_index():
  mapping = {
      "settings": {
          "number_of_shards": 1,
          "number_of_replicas": 0,
          "analysis": {
              "analyzer": {
                  "default": {
                      "type": "russian"
                  }
              }
          }
      },
      "mappings": {
          "properties": {
              # --- Базовые поля (обязательные) ---
              "product_id": {"type": "keyword"},  # keyword — для точного поиска и агрегаций
              "user_id": {"type": "keyword"},
              "total_coast": {"type": "keyword"},
              "date_search": {
                  "type": "date",
                  "format": "dd.MM.yyyy HH:mm:ss||strict_date_optional_time"
              },

              # --- Информация о продукте ---
              "product_name": {
                  "type": "text",
                  "analyzer": "russian",  # русский стеммер/лемматизация
                  "fields": {
                      "keyword": {"type": "keyword", "ignore_above": 256}  # для сортировки/агрегаций
                  }
              },
              "product_description": {
                  "type": "text",
                  "analyzer": "russian",
                  "copy_to": "full_text"  # см. ниже
              },
              "product_manufacturer": {
                  "type": "keyword"
              },
              "product_image_url": {
                  "type": "keyword"
              },
              "product_created_at": {
                  "type": "date",
                  "format": "date_time"
              },

              # --- Информация о пользователе ---
              "user_uuid": {"type": "keyword"},
              "user_fio": {
                  "type": "text",
                  "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
              },
              "user_email": {"type": "keyword"},
              "user_directorate": {"type": "keyword"},  # напр. "Дирекция по маркетингу"
              "user_work_position": {"type": "keyword"},  # "Программист"
              "user_office": {"type": "long"},
              "user_department": {"type": "keyword"},  # "Отдел WEB-маркетинга"
              "user_work_city": {"type": "keyword"},  # "Саратов"
              "user_work_phone": {"type": "keyword"},  # телефон может содержать '5219' или "+7 (999) 123-45-67"

              # --- Доп. поля для полнотекстового поиска ---
              # "full_text": {
              #     "type": "text",
              #     "analyzer": "russian",
              #     "fields": {
              #         "trigram": {
              #             "type": "text",
              #             "analyzer": "trigram_analyzer"
              #         }
              #     }
              # },

              # --- Параметры из selection_json ---
              # Используем dynamic: true для гибкости, но задаём шаблоны
              "parameters": {
                  "type": "object",
                  "dynamic": True
              }
          },
          "dynamic_templates": [
              # 1. long_* → тип long (например, "long_123")
              {
                  "longs_as_strings": {
                      "path_match": "parameters.long_*",
                      "mapping": {"type": "long"}
                  }
              },
              # 2. *_text → text (например, "product_text")
              {
                  "strings_as_text": {
                      "path_match": "parameters.*_text",
                      "mapping": {"type": "text", "analyzer": "russian"}
                  }
              },
              # 3. Другие строки → keyword (для точного поиска)
              {
                  "strings_as_keywords": {
                      "path_match": "parameters.*",
                      "match_mapping_type": "string",
                      "mapping": {"type": "keyword"}
                  }
              },
              # 4. Массивы строк → keyword[] (если не указано иное)
              {
                  "arrays_of_strings": {
                      "path_match": "parameters.*",
                      "match_mapping_type": "string",
                      "mapping": {"type": "keyword"}
                  }
              },
              # 5. Числа (float/int) → double/long
              {
                  "numbers_as_double": {
                      "path_match": "parameters.*",
                      "match_mapping_type": "double",
                      "mapping": {"type": "double"}
                  }
              },
              {
                  "numbers_as_long": {
                      "path_match": "parameters.*",
                      "match_mapping_type": "long",
                      "mapping": {"type": "long"}
                  }
              }
          ]
      }
  }

  if not es.indices.exists(index=RECOGNITION_INDEX):
      # Создаём альтернативный анализатор для partial match (опционально)
      es.indices.create(
          index=RECOGNITION_INDEX,
          body=mapping
      )
  return True