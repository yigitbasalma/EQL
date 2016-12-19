# EQL
## Amaç
Web server ve uygulama arasında yer alarak gelen istekleri karşılamak ve backend sunuculara daha az yük gitmesini sağlamak.
## Yapı
Web server ve uygulama arasında yer alarak gelen istekleri karşılar ve sonrasında couchbase içerisinde istenen key var mı diye kontrol eder.( Varsayılan olarak key, istek yapılan URL in md5 hashlenmiş halidir. ) Eğer istek yapılan item bucket'ta yer alıyorsa istek cacheden cevaplanır.Uygulama iki ana bucket kullanır.Bunlar;
+ cache_bucket : Itemlerin tutulduğu ana bucket'tır.Data, bytearray halinde burada tutulur.
+ statistic_bucket : Burada cache'te yer alan iteme ait istatisliksel bilgiler tutulmaktadır.Liste formatında olan bu data sırasıyla,
  + iteme kaç kere istek geldi,
  + cache ne zaman oluştu,
  + iteme ait mime type bilgisi.

## Kabiliyetler
Uygulama 2 ana kabiliyet üzerine kurulmuştur.Bunlar;
+ Backend sunucularından gelen imaj dosyalarını bytearray formatında cache'de tutmak.
+ Diskten dönülen statik içeriklerin bytearray formatında cache'de tutmak.
Uygulama bu fonksiyonları yerine getirirken web sunucu ve backend sunucular arasında yer alacağı düşünüldüğünden, cluster bir yapı sağlamak ve yüksek erişilebilirlik için gerekli aksiyonlar da düşünülmüştür.Uygulama config dosyasında ve örnekleme sırasında verilecek parametrelerle yedekli bir yapıyla çalışabilmektedir.

## Konfigürasyon dosyası ve Örnekleme
Konfigürasyon parametreleri ve anlamları aşağıda listelenmiştir.
+ [env]
  + cbuser : Couchbase kullanıcı adı. ( İleride couchbase optimizasyon ve kontrolleri için gerekecektir. )
  + cbpass : Couchbase kullanıcı şifresi. ( İleride couchbase optimizasyon ve kontrolleri için gerekecektir. )
  + cbhost: Couchbase hostname yada ip adresi.
  + cache_bucket : Bytearray formatındaki cache'lerin tutulacağı bucket.
  + statistic_bucket : Bytearray cache'lere ait istatislik bilgilerinin tutualacağı bucket. 
  + server : Backetn server hostname yada ip adresi.
  + cluster : Backend sunucularınız ( Eğer örnekleme sırasında "clustered=True" kullanılacaksa tanımlanması zorunludur. )
  + health_check_url : Sunuculara yapılacak health check isteği için adres. ( Eğer örnekleme sırasında "watcher=True" kullanılacaksa  zorunludur. )
  + timeout : Backend serverlara yapılacak isteğin ne kadar süre sonra timeout isteği alacağını belirtir.
  + root_directory : Statik dosya içeriklerinin aranacağı ana path ( Eğer örnekleme sırasında "with_static=True" kullanılacaksa zorunludur. )
  + check_interval : Sunucuların kaç saniyede bir health check yapacağını belirtir.Varsayılan değer 3 saniyedir.
+ [log]
  + path : Log dosyasının oluşacağı klasörü belirtir.
  
  Örnek örnekleme aşağıda yer almaktadır.
  ```
  import eql
  # En sade haliyle örnekleme
  eql = eql.EQL()
  # Cluster ile örnekleme
  eql = eql.EQL(clustered=True)
  # Cluster + watcher
  eql = eql.EQL(clustered=True, watcher=True)
  # Cluster + watcher + statik dosya desteği
  eql = eql.EQL(clustered=True, with_static=True, watcher=True)
  
  # Çalıştırmak için sadece istek yapılan adresi parametre olarak verin
  eql.route_request(url)
  ```
