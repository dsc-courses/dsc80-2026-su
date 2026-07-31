# Local-only compatibility for Liquid 4 + Ruby >= 3.2 (taint APIs removed).
class Object
  def tainted?
    false
  end

  def taint
    self
  end

  def untaint
    self
  end
end
