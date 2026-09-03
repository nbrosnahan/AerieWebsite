{{- /* Post filenames are YYYY-MM-DD-<slug>.md; strip the date prefix so it
       leaks into neither the generated title nor the URL. See CLAUDE.md ->
       "Post filenames and URLs". */ -}}
{{- $slug := replaceRE "^[0-9]{4}-[0-9]{2}-[0-9]{2}-" "" .File.ContentBaseName -}}
---
title: '{{ replace $slug "-" " " | title }}'
date: {{ .Date }}
lastmod: {{ .Date }}
# description: short fragment, no period, no URLs
description: ""
tags: []
categories: []
draft: true
slug: "{{ $slug }}"
# url: ""
# aliases: []
# weight: 0
---
