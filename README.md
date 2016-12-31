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
  + static_file_expire : CSS, JS gibi dosyaların expire süresini belirtir.
  + img_file_expire : İmaj dosyaları için expire süresini belirtir.( İlerleyen zamanlarda imaj türleri için sınırlama ve kontrol de getirilecektir. )
  + lb_db : Cluster sunucularının durumlarının tutulacağı sqlite db dosyasıdır. ( Eğer örnekleme sırasında "clustered=True" veya "watcher=True" kullanılacaksa tanımlanması zorunludur. )
+ [log]
  + path : Log dosyasının oluşacağı klasörü belirtir.
  Örnek örnekleme aşağıda yer almaktadır.Sınıf, ilk parametre olarak, scriptin başında oluşturulan logger objesini bekler.eql örneklenmeden önce mutlaka loggger sınıfı örneklenmelidir.
  ```
  import eql
  import LogMaster
  
  # Logger sınıfı
  logger = LogMaster.Logger("<dosya_adı>", "/path/to/<config_cfg_dosyası>")
  # En sade haliyle örnekleme
  eql = eql.EQL(logger)
  # Cluster ile örnekleme
  eql = eql.EQL(logger, clustered=True)
  # Cluster + watcher
  eql = eql.EQL(logger, clustered=True, watcher=True)
  # Cluster + watcher + statik dosya desteği
  eql = eql.EQL(logger, clustered=True, with_static=True, watcher=True)
  
  # Çalıştırmak için sadece istek yapılan adresi parametre olarak verin
  eql.route_request(url)
  ```
  
  Sistem **clustered** özelliği ile açıldığında "lb_db" parametresinde yer alan dosyada sqlite tablosu oluşur ve cluster durumu burada saklanır.Eğer **watcher** özelliği açılmamışsa aktif cluster bilgisi ve cluster da yer alan sunucuların durumu bir defaya mahsuu kontrol edilir ve buraya işlenir.Bu işlemden sonra eğer bir sebepten sunucular down olursa script bundan haberdar olmayacaktır.Bu nedenle **clustered** parametresiyle birlikte **watcher** parametresini de kullanmanız önerilir.Bu parametreyle birlikte, belirlenen aralıklar sunucular kontrol edilir ve down olan sunucularınıza trafik gitmez.Ayrıca sunucu durumunuzu loglardan takip edebilirsiniz.

  Yeni yaptığım güncellemede bellekte tutulan sqlite veri tabanını bir dosya olarak tutmaya karar verdim.Bunun sebebi, gunicorn kullanarak işlem başlattığım için, tüm işlem birimlerinin aynı db ye bağlanmasını sağlamak.

## Version 3.0 ( Beta )
Uygulamaya eklenen veri merkezi özelliğiyle, tam anlamıyla bir CDN özelliği kazandırılmaya çalışılmıştır.Şuan için tasarım ve bir miktar test kodu olarak hazır olan özellik, önümüzdeki dönemlerde test edilecektir.Şuan için yapılan eklentilerin, mevcut çalışma sistemine olumsuz bir etkisi yoktur.

### Amaç
Bu özelliğin uygulamaya katılmasıyla birlikte dağıtık bir yapı kurulabilir, kullanıcıların geldiği bölgerele göre ( şuan için sadece kıta olarak kontrol yapılıyor.Daha sonraları bunu daha da eleyerek bir yönlendirme yapılacak. ) en yakında bulunan veri merkezinden yanıt dönülebilir.

### İşleyiş
Belirlenecek merkez lokasyonda "router_mod" özelliğiyle modül başlatılır ve ilgili konfigürasyon dosyası düzenlenir. ( cdn.cfg ) Burada, gelen istekler bölgelere göre ayrılır ve konfig dosyasına göre ilgili veri merkezlerine yönlendirilir. ( 302 koduyla )

### Konfigürasyon Dosyası
+ [env]
  + edge_locations : Veri merkezlerinin hangi kıtalarda olduğunu belirtir.
  + default_edge : Gelen isteğin ait olduğu bölgeye hizmet verecek bir veri merkezi olmaması halinde isteğin hangi merkezden karşılanacağını belirtir.
  + edge_check_interval : Veri merkezlerinde bulunan sunucuların kaç saniyede bir kontrol edileceğini belirtir.
  + continent_db : Kıta ve ülke kodlarının eşleştirildiği veri tabanı dosyasının lokasyonunu belirtir.Burada bulunan parametre aslında bir sabittir ve değiştirilmemesi tavsiye edilir.
  + lb_db : Veri merkezlerinde bulunan sunucuların durumlarının tutulacağı veri tabanı dosyasının yolunu ve adını belirtir.
+ [<veri_merkezi_kıta_kodu>]
  + servers : Veri merkezinde barındırılan sunuculara ait hostname yada ip bilgisi. ( burada hostname kullanmanız tavsiye edilmektedir. )
  + timeout : Veri merkezinde barındırılan sunuculara ulaşılması sırasında isteğin ne kadar sürede zaman aşımına uğrayacağını belirtir.
  + health_check_url : Veri merkezinde barındırılan sunuculara ait kontrol adresleridir. ( Bu adres modül içerisinde bir end point olarak verilecektir. )

### Örnekleme
Sistemin kullanılabilmesi için aşağıdaki örnekleme yeterlidir.

```
import eql
import logMaster

logger = LogMaster.Logger("rest_service_router_mode", "/EQL/source/config.cfg")
eql = eql.EQL(logger, router_mod=True)
```
